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
