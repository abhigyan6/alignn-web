import { test, expect } from "@playwright/test";

test("policy pages stay public when authentication scripts are unavailable", async ({
  page,
}) => {
  await page.route(/clerk.*\.(js)|clerk\.browser\.js/, (route) =>
    route.abort(),
  );
  for (const [path, title] of [
    ["/privacy", "Privacy policy"],
    ["/terms", "Terms & conditions"],
    ["/cookies", "Cookie information"],
  ]) {
    await page.goto(path);
    await expect(
      page.getByRole("heading", { level: 1, name: title, exact: true }),
    ).toBeVisible();
    await expect(
      page
        .locator("main")
        .getByRole("link", { name: "contact@onlyward.app", exact: true }),
    ).toHaveAttribute("href", "mailto:contact@onlyward.app");
    await expect(page.locator("main")).toContainText("Pre-launch draft");
    await page.setViewportSize({ width: 319, height: 800 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});

test("cookie notice dismissal persists and policies remain reachable", async ({
  page,
}) => {
  await page.goto("/cookies");
  const notice = page.getByRole("complementary", {
    name: "Cookie information",
  });
  await expect(notice).toBeVisible();
  await page
    .getByRole("button", { name: "Dismiss notice", exact: true })
    .click();
  await expect(notice).toHaveCount(0);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Cookie information", exact: true }),
  ).toBeVisible();
  await expect(notice).toHaveCount(0);
  await expect(
    page
      .getByRole("navigation", { name: "Support and policies" })
      .getByRole("link", { name: "Privacy", exact: true }),
  ).toHaveAttribute("href", "/privacy");
});
