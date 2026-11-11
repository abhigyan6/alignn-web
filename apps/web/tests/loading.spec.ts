import { test, expect } from "@playwright/test";

test("welcome reveal runs once per tab and clears without blocking navigation", async ({
  page,
}) => {
  await page.goto("/");
  await expect
    .poll(() =>
      page.evaluate(() => sessionStorage.getItem("alignn-intro-seen")),
    )
    .toBe("1");
  await expect(page.locator("html")).not.toHaveAttribute("data-alignn-intro", {
    timeout: 5000,
  });
  await page.reload();
  await expect(page.locator("html")).not.toHaveAttribute("data-alignn-intro");
  await expect(
    page.getByRole("heading", { name: "A clearer path is coming soon." }),
  ).toBeVisible();
});

test("discovery skeleton preserves the card grid until results arrive", async ({
  page,
}) => {
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
  await page.goto("/explore");
  await expect(page.locator(".opportunity-loading")).toBeVisible();
  await expect(page.locator(".skeleton-card")).toHaveCount(4);
  await expect(page.locator(".opportunity-loading")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await expect(
    page
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("link", { name: "Discover", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.locator("html")).not.toHaveAttribute("data-alignn-intro", {
    timeout: 5000,
  });
  await page.screenshot({
    path: `/tmp/alignn-skeleton-${test.info().project.name}.png`,
    fullPage: true,
  });
  release();
  await expect(page.locator(".opportunity-loading")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Your next chapter is on its way." }),
  ).toBeVisible();
});

test("reduced motion disables loader movement and the welcome overlay", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  expect(
    await page
      .locator(".site-intro")
      .evaluate((element) => getComputedStyle(element).display),
  ).toBe("none");
  expect(
    await page
      .locator(".brand-loader-orbit")
      .first()
      .evaluate((element) => getComputedStyle(element).animationName),
  ).toBe("none");
});
