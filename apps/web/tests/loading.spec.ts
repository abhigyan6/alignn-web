import { test, expect, type Page } from "@playwright/test";

async function holdDiscovery(page: Page) {
  let release: () => void = () => {};
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/opportunities*", async (route) => {
    await pending;
    await route.fulfill({
      json: { items: [], ranking_status: "NOT_REQUESTED", next_cursor: null },
    });
  });
  return release;
}

test("public page stays available without an artificial welcome overlay", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("main")).toBeVisible();
  await expect(page.locator("main h1")).toBeVisible();
  await expect(page.locator(".site-intro")).toHaveCount(0);
  await expect(page.locator("html")).not.toHaveAttribute("data-alignn-intro");
  await page.reload();
  await expect(page.locator("main h1")).toBeVisible();
  await expect(page.locator(".site-intro")).toHaveCount(0);
});

test("pending discovery uses complete short-card placeholders without hiding controls", async ({
  page,
}) => {
  const release = await holdDiscovery(page);
  try {
    await page.goto("/explore");
    await expect(page.locator(".opportunity-loading")).toBeVisible();
    await expect(page.locator(".skeleton-card")).toHaveCount(4);
    await expect(page.locator(".opportunity-loading")).toHaveAttribute(
      "aria-busy",
      "true",
    );
    const first = page.locator(".skeleton-card").first();
    for (const part of [
      "logo",
      "category",
      "title",
      "metadata",
      "skills",
      "footer",
    ]) {
      await expect(
        first.locator(`[data-skeleton-part="${part}"]`),
      ).toBeVisible();
    }
    await expect(page.getByRole("search")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Internships", exact: true }),
    ).toBeEnabled();
    const dimensions = await first.boundingBox();
    expect(dimensions?.height).toBeGreaterThanOrEqual(220);
    expect(dimensions?.height).toBeLessThanOrEqual(320);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await expect(page.locator(".site-intro")).toHaveCount(0);
  } finally {
    release();
  }
  await expect(page.locator(".opportunity-loading")).toHaveCount(0);
});

test("reduced motion leaves static usable loading placeholders", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const release = await holdDiscovery(page);
  try {
    await page.goto("/explore");
    const first = page.locator(".skeleton-card").first();
    await expect(first).toBeVisible();
    expect(
      await first.evaluate(
        (element) => getComputedStyle(element, "::after").animationName,
      ),
    ).toBe("none");
    await expect(page.locator(".site-intro")).toHaveCount(0);
    await expect(page.getByRole("search")).toBeVisible();
  } finally {
    release();
  }
  await expect(page.locator(".opportunity-loading")).toHaveCount(0);
});
