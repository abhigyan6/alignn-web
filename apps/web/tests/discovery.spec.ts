import { test, expect } from "@playwright/test";
test("discovery loads real API and keeps filters usable", async ({ page }) => {
  await page.goto("/explore");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Find your people",
  );
  await expect(
    page.getByRole("searchbox", { name: "Search opportunities" }),
  ).toBeVisible();
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
test("invalid login never shows a signed in workspace", async ({ page }) => {
  await page.goto("/login");
  await page
    .getByLabel("Email", { exact: true })
    .fill("not-an-account@alignn.test");
  await page.getByLabel("Password", { exact: true }).fill("Wrong-password-42!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Invalid email or password",
  );
  await expect(page).toHaveURL(/\/login$/);
});
test("verification with missing token gives useful feedback", async ({
  page,
}) => {
  await page.goto("/verify-email");
  await page.getByRole("button", { name: "Verify email", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "missing its token",
  );
});
