import { test, expect } from "@playwright/test";

test("signup and sign-in share their responsive shell and form styling", async ({
  page,
}) => {
  const backgrounds: string[] = [];
  for (const route of ["/login", "/signup"]) {
    await page.goto(route);
    await expect(page.locator(".auth-shell")).toBeVisible();
    await expect(
      page.getByLabel("Email address", { exact: true }),
    ).toBeVisible();
    await expect(page.locator(".auth-clerk-root")).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Continue browsing first" }),
    ).toHaveAttribute("href", "/explore");
    await expect(page.locator("html")).not.toHaveAttribute(
      "data-alignn-intro",
      { timeout: 5000 },
    );
    backgrounds.push(
      await page
        .locator(".auth-panel")
        .evaluate((element) => getComputedStyle(element).backgroundColor),
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `/tmp/alignn-${route.slice(1)}-${test.info().project.name}.png`,
      fullPage: true,
    });
  }
  expect(backgrounds[0]).toBe(backgrounds[1]);
  await expect(
    page.getByRole("link", { name: "Sign in", exact: true }),
  ).toHaveAttribute("href", /\/login/);
});
