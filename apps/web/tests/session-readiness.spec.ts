import { test, expect, type Page, type Route } from "@playwright/test";
import {
  ANONYMOUS_SESSION,
  getSessionKey,
  isSessionReady,
  markSessionPending,
  markSessionReady,
  sessionKeyFor,
  waitForSession,
} from "../src/lib/session-readiness";
import { ApiError, isPublicCatalogRead } from "../src/lib/api";
import {
  resolveSaved,
  savedSnapshotFor,
  withSaved,
} from "../src/lib/saved-ids";

const fixture = {
  id: "00000000-0000-0000-0000-000000000042",
  title: "Readiness fixture internship",
  organization_name: "Readiness test fixture",
  kind: "INTERNSHIP",
  location: "Pune",
  work_mode: "REMOTE",
  description: "Synthetic fixture description.",
  apply_url: "https://example.com/apply",
  source_url: "https://example.com/listing",
  registration_closes_at: null,
  source_name: "Test fixture",
  required_skills: [],
  preferred_skills: [],
};

test.describe("session key contract", () => {
  test.afterEach(() => markSessionPending());

  test("public catalog reads skip the wait; account reads and mutations do not", () => {
    expect(isPublicCatalogRead("/opportunities?sort=deadline&limit=3")).toBe(
      true,
    );
    expect(isPublicCatalogRead("/opportunities/abc")).toBe(true);
    expect(isPublicCatalogRead("/me/saved")).toBe(false);
    expect(isPublicCatalogRead("/opportunities/abc/fit")).toBe(false);
    expect(isPublicCatalogRead("/opportunities/abc/save", "POST")).toBe(false);
    expect(isPublicCatalogRead("/opportunities/abc", "DELETE")).toBe(false);
  });

  test("pending has no key; ready names who the session belongs to", () => {
    markSessionPending();
    expect(getSessionKey()).toBeNull();
    expect(isSessionReady()).toBe(false);
    markSessionReady(null);
    expect(getSessionKey()).toBe(ANONYMOUS_SESSION);
    markSessionReady("user_a");
    expect(getSessionKey()).toBe(sessionKeyFor("user_a"));
    expect(isSessionReady()).toBe(true);
  });

  test("sign-in, sign-out and account switch each change the key while ready", () => {
    markSessionReady(null);
    const anonymous = getSessionKey();
    markSessionReady("user_a");
    const a = getSessionKey();
    markSessionReady("user_b");
    const b = getSessionKey();
    markSessionReady(null);
    expect(new Set([anonymous, a, b]).size).toBe(3);
    expect(getSessionKey()).toBe(anonymous);
  });

  test("waitForSession resolves when readiness arrives", async () => {
    markSessionPending();
    const waiting = waitForSession();
    markSessionReady("user_a");
    await expect(waiting).resolves.toBe(true);
  });

  test("waitForSession resolves at once when already ready", async () => {
    markSessionReady(null);
    await expect(waitForSession()).resolves.toBe(true);
  });

  test("waitForSession rejects on abort and ignores later readiness", async () => {
    markSessionPending();
    const controller = new AbortController();
    const waiting = waitForSession(controller.signal);
    controller.abort();
    await expect(waiting).rejects.toBeDefined();
    markSessionReady("user_a");
    expect(getSessionKey()).toBe(sessionKeyFor("user_a"));
  });

  test("waitForSession rejects at once for an already aborted signal", async () => {
    markSessionPending();
    const controller = new AbortController();
    controller.abort();
    await expect(waitForSession(controller.signal)).rejects.toBeDefined();
  });

  test("waitForSession resolves false after the timeout", async () => {
    markSessionPending();
    const realSetTimeout = globalThis.setTimeout;
    globalThis.setTimeout = ((fn: () => void) =>
      realSetTimeout(fn, 5)) as unknown as typeof setTimeout;
    try {
      await expect(waitForSession()).resolves.toBe(false);
    } finally {
      globalThis.setTimeout = realSetTimeout;
    }
  });
});

test.describe("saved state resolution", () => {
  const keyA = sessionKeyFor("user_a");
  const keyB = sessionKeyFor("user_b");

  test("nothing is claimed while the session is pending", () => {
    const snapshot = savedSnapshotFor(keyA, { items: [{ id: "x" }] });
    expect(resolveSaved(snapshot, null)).toEqual({
      status: "loading",
      ids: new Set(),
    });
    expect(resolveSaved(null, keyA).status).toBe("loading");
  });

  test("one account's saved IDs are never shown for another", () => {
    const snapshot = savedSnapshotFor(keyA, { items: [{ id: "x" }] });
    expect(resolveSaved(snapshot, keyA)).toEqual({
      status: "ready",
      ids: new Set(["x"]),
    });
    // Account switch: same readiness, different key.
    expect(resolveSaved(snapshot, keyB)).toEqual({
      status: "loading",
      ids: new Set(),
    });
    // Sign-out.
    expect(resolveSaved(snapshot, ANONYMOUS_SESSION).ids.size).toBe(0);
  });

  test("a 401 means signed out: ready and empty", () => {
    const snapshot = savedSnapshotFor(ANONYMOUS_SESSION, {
      error: new ApiError(401, "Sign in"),
    });
    expect(snapshot.status).toBe("ready");
    expect(snapshot.ids.size).toBe(0);
  });

  test("any other failure is unknown, not an empty saved list", () => {
    for (const error of [
      new ApiError(500, "boom"),
      new ApiError(503, "down"),
      new ApiError(0, "Your account is still loading."),
      new TypeError("Failed to fetch"),
    ]) {
      const snapshot = savedSnapshotFor(keyA, { error });
      expect(resolveSaved(snapshot, keyA).status).toBe("unknown");
    }
  });

  test("save and remove update a known set only", () => {
    const known = savedSnapshotFor(keyA, { items: [{ id: "x" }] });
    const added = withSaved(known, keyA, "y", true);
    expect(added && [...added.ids].sort()).toEqual(["x", "y"]);
    const removed = withSaved(added, keyA, "x", false);
    expect(removed && [...removed.ids]).toEqual(["y"]);
    // Other account's snapshot is untouched.
    expect(withSaved(known, keyB, "y", true)).toBe(known);
    // An unknown set stays unknown rather than becoming a claim.
    const unknown = savedSnapshotFor(keyA, { error: new ApiError(500, "x") });
    expect(withSaved(unknown, keyA, "y", true)).toBe(unknown);
    expect(withSaved(null, keyA, "y", true)).toBeNull();
  });
});

async function mockCatalog(page: Page) {
  await page.route("**/api/v1/opportunities/*", (route) =>
    route.fulfill({ json: fixture }),
  );
  await page.route("**/api/v1/opportunities?*", (route) =>
    route.fulfill({
      json: {
        items: [fixture],
        ranking_status: "SIGN_IN_REQUIRED",
        next_cursor: null,
      },
    }),
  );
}

/**
 * The app has two runtime modes, and the page itself says which one it is in:
 * - Clerk configured but unreachable: the header shows the loading-account
 *   placeholder and the session never becomes ready.
 * - Clerk not configured: the header shows "Sign in" and the session is ready
 *   at once, so account reads are legitimate.
 * Exactly one of them must be visible, so this cannot pass by seeing neither.
 */
async function sessionMode(page: Page): Promise<"blocked" | "unconfigured"> {
  const placeholder = page.locator(".account-placeholder");
  const signIn = page
    .locator(".header-account")
    .getByRole("link", { name: "Sign in" });
  await expect(placeholder.or(signIn)).toBeVisible();
  return (await placeholder.isVisible()) ? "blocked" : "unconfigured";
}

test.describe("public discovery while Clerk is blocked", () => {
  test.beforeEach(async ({ page }) => {
    // Simulate slow/unavailable Clerk by failing any Clerk network request.
    await page.route(
      (url) => url.hostname.includes("clerk"),
      (route) => route.abort(),
    );
  });

  test("Discover and details stay readable and send no account read before readiness", async ({
    page,
  }) => {
    const savedRequests: string[] = [];
    await page.route("**/api/v1/me/saved", (route) => {
      savedRequests.push(route.request().url());
      return route.fulfill({ status: 401, json: { error: { message: "x" } } });
    });
    await mockCatalog(page);
    await page.goto("/explore");
    await expect(page.getByRole("heading", { level: 3 })).toHaveText(
      fixture.title,
    );
    const mode = await sessionMode(page);
    if (mode === "blocked") {
      // Give a premature account read time to show up before asserting none did.
      await page.waitForTimeout(1000);
      expect(savedRequests).toEqual([]);
      await expect(
        page.getByRole("button", { name: /Checking saved status/ }),
      ).toBeDisabled();
    } else {
      await expect.poll(() => savedRequests.length).toBeGreaterThan(0);
    }
    await page.getByRole("link", { name: fixture.title }).click();
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      fixture.title,
    );
    await expect(
      page.getByRole("link", { name: /^Apply on / }),
    ).toHaveAttribute("href", fixture.apply_url);
  });

  test("home preview cards stay visible with a disabled, labelled save control", async ({
    page,
  }) => {
    const savedRequests: string[] = [];
    await page.route("**/api/v1/me/saved", (route) => {
      savedRequests.push(route.request().url());
      return route.fulfill({ status: 401, json: { error: { message: "x" } } });
    });
    await mockCatalog(page);
    await page.goto("/");
    const card = page.locator(".opportunity-card").first();
    await expect(card).toContainText(fixture.title);
    const mode = await sessionMode(page);
    test.skip(
      mode !== "blocked",
      "Clerk is not configured here, so the session is ready immediately.",
    );
    await page.waitForTimeout(1000);
    expect(savedRequests).toEqual([]);
    const save = card.locator(".bookmark-button");
    await expect(save).toBeDisabled();
    await expect(save).toHaveAttribute("aria-label", /Checking saved status/);
  });
});

test.describe("saved state once the session is ready", () => {
  // These need the session to be ready, which happens at once only when Clerk
  // is not configured. They are skipped, not passed, when Clerk is configured.
  async function openReady(page: Page, path: string) {
    await page.goto(path);
    const mode = await sessionMode(page);
    test.skip(
      mode !== "unconfigured",
      "Clerk is configured here, so readiness depends on the provider.",
    );
  }

  const saved = (route: Route, ids: string[]) =>
    route.fulfill({ json: { items: ids.map((id) => ({ ...fixture, id })) } });

  test("home and Discover cards reflect the actual saved IDs", async ({
    page,
  }) => {
    await mockCatalog(page);
    await page.route("**/api/v1/me/saved", (route) =>
      saved(route, [fixture.id]),
    );
    for (const path of ["/", "/explore"]) {
      await openReady(page, path);
      await expect(
        page.getByRole("button", { name: `Remove saved ${fixture.title}` }),
      ).toHaveAttribute("aria-pressed", "true");
    }
  });

  test("a signed-out 401 shows cards as not saved and saving stays available", async ({
    page,
  }) => {
    await mockCatalog(page);
    await page.route("**/api/v1/me/saved", (route) =>
      route.fulfill({ status: 401, json: { error: { message: "x" } } }),
    );
    await openReady(page, "/explore");
    const save = page.getByRole("button", { name: `Save ${fixture.title}` });
    await expect(save).toBeEnabled();
    await expect(save).toHaveAttribute("aria-pressed", "false");
  });

  test("a failed read stays unknown, disables saving, and recovers on retry", async ({
    page,
  }) => {
    await mockCatalog(page);
    let calls = 0;
    await page.route("**/api/v1/me/saved", (route) => {
      calls += 1;
      return calls === 1
        ? route.fulfill({
            status: 500,
            json: { error: { message: "Temporary failure" } },
          })
        : saved(route, [fixture.id]);
    });
    await openReady(page, "/explore");
    await expect(
      page.getByText("We couldn’t check your saved opportunities right now."),
    ).toBeVisible();
    const checking = page.getByRole("button", {
      name: `Checking saved status for ${fixture.title}`,
    });
    await expect(checking).toBeDisabled();
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(
      page.getByRole("button", { name: `Remove saved ${fixture.title}` }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(calls).toBe(2);
  });

  test("details keep Save disabled until the saved state is known, then reflect it", async ({
    page,
  }) => {
    await mockCatalog(page);
    await page.route("**/api/v1/me/saved", (route) =>
      saved(route, [fixture.id]),
    );
    await openReady(page, `/opportunities/${fixture.id}`);
    await expect(page.getByRole("button", { name: /^Saved$/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  test("details offer a retry when the saved read fails", async ({ page }) => {
    await mockCatalog(page);
    let calls = 0;
    await page.route("**/api/v1/me/saved", (route) => {
      calls += 1;
      return calls === 1
        ? route.fulfill({ status: 500, json: { error: { message: "x" } } })
        : saved(route, []);
    });
    await openReady(page, `/opportunities/${fixture.id}`);
    await expect(
      page.getByRole("button", { name: "Save opportunity" }),
    ).toBeDisabled();
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(
      page.getByRole("button", { name: "Save opportunity" }),
    ).toBeEnabled();
  });
});
