import { test, expect } from "@playwright/test";

const fixture = {
  id: "00000000-0000-0000-0000-000000000099",
  title: "Student buildathon fixture",
  organization_name: "Synthetic UI fixture",
  kind: "HACKATHON",
  mode: "EXTERNAL",
  status: "PUBLISHED",
  location: "Bhopal, India",
  work_mode: "ONSITE",
  registration_closes_at: null,
  starts_at: null,
  ends_at: null,
  apply_url: "https://example.org/application",
  source_url: "https://example.org/listing",
  source_name: "Synthetic fixture",
  required_skills: [],
  preferred_skills: [],
  description: "A synthetic listing used only for browser tests.",
};

test("home explains the product and category links open the matching feed", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Find opportunities",
  );
  await expect(page.getByText("Coming soon", { exact: false })).toHaveCount(0);
  await page.getByRole("link", { name: "Hackathons", exact: true }).click();
  await expect(page).toHaveURL(/kind=HACKATHON/);
  await expect(
    page.getByRole("button", { name: "Hackathons", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("background ranking refresh retains useful cards", async ({ page }) => {
  await page.clock.install();
  let requests = 0,
    release: () => void = () => {};
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/opportunities?*", async (route) => {
    requests++;
    if (requests > 1) await pending;
    await route.fulfill({
      json: { items: [fixture], ranking_status: "PENDING", next_cursor: null },
    });
  });
  await page.goto("/explore");
  await expect(
    page.getByRole("heading", { name: fixture.title }),
  ).toBeVisible();
  await page.clock.runFor(5100);
  await expect.poll(() => requests).toBeGreaterThan(1);
  await expect(
    page.getByRole("heading", { name: fixture.title }),
  ).toBeVisible();
  await expect(page.locator(".skeleton-card")).toHaveCount(0);
  release();
});

test("failed category refresh cannot reuse the previous next-page cursor", async ({
  page,
}) => {
  await page.route("**/api/v1/opportunities?*", (route) =>
    route.request().url().includes("kind=INTERNSHIP")
      ? route.fulfill({
          status: 500,
          json: { error: { message: "Controlled test failure" } },
        })
      : route.fulfill({
          json: {
            items: [fixture],
            ranking_status: "NOT_REQUESTED",
            next_cursor: 12,
          },
        }),
  );
  await page.goto("/explore");
  await expect(
    page.getByRole("button", { name: "Next opportunities" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Internships", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Controlled test failure",
  );
  await expect(
    page.getByRole("button", { name: "Next opportunities" }),
  ).toHaveCount(0);
});

test("saving is separate from opening a listing and redirects signed-out students", async ({
  page,
}) => {
  await page.route("**/api/v1/opportunities?*", (route) =>
    route.fulfill({
      json: {
        items: [fixture],
        ranking_status: "NOT_REQUESTED",
        next_cursor: null,
      },
    }),
  );
  // A signed-out student's saved read is a 401: nothing is saved, and the
  // save control becomes available once that is known.
  await page.route("**/api/v1/me/saved", (route) =>
    route.fulfill({
      status: 401,
      json: { error: { message: "Sign in to continue." } },
    }),
  );
  await page.route(`**/api/v1/opportunities/${fixture.id}/save`, (route) =>
    route.fulfill({
      status: 401,
      json: { error: { message: "Sign in to continue." } },
    }),
  );
  await page.goto("/explore");
  const card = page.locator(".opportunity-card").first();
  await expect(card.getByRole("link", { name: fixture.title })).toHaveAttribute(
    "href",
    `/opportunities/${fixture.id}`,
  );
  await card
    .getByRole("button", { name: `Save ${fixture.title}`, exact: true })
    .click();
  await expect(page).toHaveURL(/\/login/);
});

test("closed detail preserves history without an active apply action", async ({
  page,
}) => {
  await page.route(`**/api/v1/opportunities/${fixture.id}`, (route) =>
    route.fulfill({ json: { ...fixture, status: "CLOSED" } }),
  );
  await page.goto(`/opportunities/${fixture.id}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    fixture.title,
  );
  await expect(
    page.getByText("This opportunity is closed.", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /^Apply on/ })).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Track this application" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Read the original listing" }),
  ).toHaveAttribute("href", fixture.source_url);
});

test("public pages reflow at narrow phone, tablet and desktop widths", async ({
  page,
}) => {
  for (const width of [319, 360, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const path of ["/", "/explore"]) {
      await page.goto(path);
      await expect(page.locator(".opportunity-card").first()).toBeVisible({
        timeout: 15000,
      });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        `${path} at ${width}`,
      ).toBe(true);
    }
  }
});

test("unknown organizer attribution remains qualified", async ({ page }) => {
  await page.route("**/api/v1/opportunities?*", (route) =>
    route.fulfill({
      json: {
        items: [
          {
            ...fixture,
            organization_name: "Organizer listed on Devfolio",
            source_name: "Devfolio",
          },
        ],
        ranking_status: "NOT_REQUESTED",
        next_cursor: null,
      },
    }),
  );
  await page.goto("/explore");
  await expect(page.locator(".opportunity-company")).toHaveText("Via Devfolio");
});

test("mobile fit failure has a nearby sign-in recovery", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.route(`**/api/v1/opportunities/${fixture.id}`, (route) =>
    route.fulfill({
      json: {
        ...fixture,
        description: "Long source description.\n\n".repeat(200),
      },
    }),
  );
  await page.route(`**/api/v1/opportunities/${fixture.id}/fit`, (route) =>
    route.fulfill({
      status: 401,
      json: { error: { message: "Sign in to continue." } },
    }),
  );
  await page.goto(`/opportunities/${fixture.id}`);
  const button = page.getByRole("button", { name: "See my profile match" });
  await button.scrollIntoViewIfNeeded();
  await button.click();
  const recovery = page.getByRole("link", { name: "Sign in to see your fit" });
  await expect(recovery).toBeVisible();
  const a = await button.boundingBox(),
    b = await recovery.boundingBox();
  expect(b!.y - a!.y).toBeGreaterThan(0);
  expect(b!.y - a!.y).toBeLessThan(250);
});
