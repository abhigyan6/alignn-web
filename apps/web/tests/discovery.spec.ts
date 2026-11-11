import { test, expect } from "@playwright/test";

test("discovery loads real API and keeps filters usable", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Find your people",
  );
  const response = page.waitForResponse(
    (r) =>
      r.url().includes("/api/v1/opportunities?") &&
      r.request().method() === "GET",
  );
  await page.getByRole("button", { name: "Internships", exact: true }).click();
  expect((await response).status()).toBe(200);
  await expect(
    page.getByRole("button", { name: "Internships", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("Clerk sign-in renders with a sign-up path", async ({ page }) => {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", {
      name: "Sign in to Alignn",
    }),
  ).toBeVisible();
  await expect(page.getByLabel("Email address", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Sign up", exact: true }),
  ).toHaveAttribute("href", /\/signup/);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

for (const route of ["/workspace", "/onboarding", "/onboarding?edit=1"]) {
  test(`${route} requires a Clerk session`, async ({ page }) => {
    await page.goto(route);
    await expect(page).toHaveURL(/\/login/);
    await expect(
      page.getByLabel("Email address", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Your workspace", exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "Make Alignn yours.", exact: true }),
    ).toHaveCount(0);
  });
}

test("legacy recovery routes use Clerk", async ({ page }) => {
  await page.goto("/reset-password?token=obsolete");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByLabel("Email address", { exact: true })).toBeVisible();
});

for (const width of [360, 390, 768, 1440]) {
  test(`long opportunity titles remain inside cards at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    const title =
      "AReallyLongUnbrokenOpportunityTitleToTestNarrowMobileCardsAndOverflow";
    await page.route("**/api/v1/opportunities*", (route) =>
      route.fulfill({
        json: {
          items: [
            {
              id: "00000000-0000-0000-0000-000000000001",
              title,
              organization_name: "Responsive test fixture",
              kind: "INTERNSHIP",
              location: "Bengaluru / Remote",
              work_mode: "REMOTE",
              registration_closes_at: null,
              source_name: "Test fixture",
            },
          ],
          ranking_status: "NOT_REQUESTED",
          next_cursor: null,
        },
      }),
    );
    await page.goto("/explore");
    const card = page.locator(".event").first();
    await expect(card).toBeVisible();
    for (const selector of [".opportunity-company", "h3"]) {
      const dimensions = await card.locator(selector).evaluate((element) => {
        const text = element.getBoundingClientRect();
        const card = element.closest(".event")!.getBoundingClientRect();
        return {
          textRight: text.right,
          cardRight: card.right,
          scroll: element.scrollWidth,
          width: element.clientWidth,
        };
      });
      expect(dimensions.textRight).toBeLessThanOrEqual(dimensions.cardRight);
      expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
    }
  });
}

test("changing category restarts an exhausted match-ranking check", async ({
  page,
}) => {
  await page.clock.install();
  let requests = 0;
  await page.route("**/api/v1/opportunities*", (route) => {
    requests += 1;
    return route.fulfill({
      json: { items: [], ranking_status: "PENDING", next_cursor: null },
    });
  });
  await page.goto("/explore");
  await expect(
    page.getByText("Your match ranking is being calculated.", { exact: false }),
  ).toBeVisible();
  for (let index = 0; index < 6; index += 1) {
    const before = requests;
    await page.clock.runFor(5100);
    await expect.poll(() => requests).toBeGreaterThan(before);
  }
  await expect(
    page.getByRole("button", { name: "Check ranking again" }),
  ).toBeVisible();
  const beforeCategory = requests;
  await page.getByRole("button", { name: "Internships", exact: true }).click();
  await expect.poll(() => requests).toBeGreaterThan(beforeCategory);
  await expect(
    page.getByText("Your match ranking is being calculated.", { exact: false }),
  ).toBeVisible();
  const afterCategory = requests;
  await page.clock.runFor(5100);
  await expect.poll(() => requests).toBeGreaterThan(afterCategory);
});

test("real internship opens consistent details with an external application link", async ({
  page,
}) => {
  await page.goto("/explore");
  await page.getByRole("button", { name: "Internships", exact: true }).click();
  const card = page.locator(".opportunity-card").first();
  await expect(card).toBeVisible();
  const title = await card.locator("h3").innerText();
  await page.screenshot({
    path: `/tmp/alignn-discovery-current-${test.info().project.name}.png`,
    fullPage: true,
  });
  await card.click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  const apply = page.getByRole("link", { name: "Apply externally" });
  await expect(apply).toHaveAttribute("href", /^https:\/\//);
  await expect(apply).toHaveAttribute("target", "_blank");
  await expect(
    page.getByRole("heading", { name: "About this opportunity" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `/tmp/alignn-detail-current-${test.info().project.name}.png`,
    fullPage: false,
  });
});
