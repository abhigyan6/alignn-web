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

test("Clerk primary actions and provider icons remain legible across layouts", async ({
  page,
}) => {
  for (const width of [319, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["/login", "/signup"]) {
      await page.goto(route);
      await expect(
        page.getByLabel("Email address", { exact: true }),
      ).toBeVisible();
      const primary = page.locator(".cl-formButtonPrimary");
      await expect(primary).toBeVisible();
      await expect(primary).toContainText("Continue");
      const appearance = await primary.evaluate((element) => {
        const style = getComputedStyle(element);
        const parse = (value: string) => {
          const values = (value.match(/[\d.]+/g) ?? []).map(Number);
          const linear = value.startsWith("color(srgb ");
          return {
            channels: values.slice(0, 3).map((v) => (linear ? v * 255 : v)),
            alpha: values[3] ?? 1,
          };
        };
        const foreground = parse(style.color),
          background = parse(style.backgroundColor);
        const luminance = (channels: number[]) =>
          channels
            .map((value) => {
              const channel = value / 255;
              return channel <= 0.04045
                ? channel / 12.92
                : ((channel + 0.055) / 1.055) ** 2.4;
            })
            .reduce(
              (sum, value, index) =>
                sum + value * [0.2126, 0.7152, 0.0722][index],
              0,
            );
        const first = luminance(foreground.channels),
          second = luminance(background.channels);
        return {
          alpha: background.alpha,
          contrast:
            (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05),
          height: element.getBoundingClientRect().height,
          width: element.getBoundingClientRect().width,
        };
      });
      expect(
        appearance.alpha,
        `${route} at ${width}px needs a painted primary button`,
      ).toBe(1);
      expect(
        appearance.contrast,
        `${route} at ${width}px primary text contrast`,
      ).toBeGreaterThanOrEqual(4.5);
      expect(appearance.height).toBeGreaterThanOrEqual(44);
      expect(appearance.width).toBeGreaterThan(100);
      const google = page.getByRole("button", {
        name: "Continue with Google",
        exact: true,
      });
      await expect(google).toBeVisible();
      const icon = google.locator(".cl-socialButtonsProviderIcon__google");
      await expect(icon).toBeVisible();
      await expect
        .poll(
          () =>
            icon.evaluate(async (element) => {
              const rect = element.getBoundingClientRect();
              const background = getComputedStyle(element).backgroundImage;
              const match = background.match(/^url\(["']?(.*?)["']?\)$/);
              if (rect.width < 12 || rect.height < 12 || !match) return false;
              // Clerk renders provider marks as CSS backgrounds, not img elements.
              const image = new Image();
              image.src = match[1];
              try {
                await image.decode();
                return image.naturalWidth > 0 && image.naturalHeight > 0;
              } catch {
                return false;
              }
            }),
          { timeout: 10000 },
        )
        .toBe(true);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.screenshot({
        path: `/tmp/alignn-auth-contrast-${route.slice(1)}-${width}-${test.info().project.name}.png`,
        fullPage: true,
      });
    }
  }
});
