import { test, expect } from "@playwright/test";

test.describe("coming-soon landing page", () => {
  test("has real metadata, one h1 and the sections in order", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page).toHaveTitle("Alignn | The missing link to your future");
    await expect(page.locator('meta[name="description"]')).toHaveAttribute(
      "content",
      /internships, jobs, hackathons/,
    );
    await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
    await expect(page.locator("h1 em")).toHaveText("future.");
    expect(
      await page.$$eval("main > section", (s) => s.map((x) => x.id || "hero")),
    ).toEqual(["hero", "why", "coming", "how", "preview", "faq", "join"]);
    await expect(page.getByText("In development").first()).toBeVisible();
    await expect(page.getByText("Planned", { exact: true })).toBeVisible();
    await expect(page.getByText("Later", { exact: true })).toBeVisible();
  });

  test("labels mock content and keeps sign-up visibly disabled", async ({
    page,
  }) => {
    await page.goto("/");
    expect(await page.locator(".lp-example").count()).toBeGreaterThanOrEqual(5);
    for (const caption of await page.locator(".lp-tile-caption").all()) {
      await expect(caption).toHaveText(/^Example/);
    }
    await expect(page.locator("#join input")).toBeDisabled();
    await expect(page.locator("#join button")).toBeDisabled();
    await expect(page.locator("#join-status")).toContainText("not connected");
  });

  test("FAQ opens one answer at a time", async ({ page }) => {
    await page.goto("/");
    const items = page.locator("#faq details");
    await items.nth(0).locator("summary").click();
    await items.nth(1).locator("summary").click();
    await expect(page.locator("#faq details[open]")).toHaveCount(1);
  });

  test("honours prefers-reduced-motion", async ({ browser }) => {
    const context = await browser.newContext({ reducedMotion: "reduce" });
    const page = await context.newPage();
    await page.goto("/");
    for (const selector of [".lp-hero", ".lp-band-track", ".lp-sticker"]) {
      await expect(page.locator(selector).first()).toHaveCSS(
        "animation-name",
        "none",
      );
    }
    for (const word of await page.locator(".lp-word").all()) {
      await expect(word).toHaveCSS("color", "rgb(12, 60, 41)");
    }
    await context.close();
  });

  test("manifesto words light up as it scrolls into view", async ({ page }) => {
    await page.goto("/");
    const lit = page.locator('.lp-word[data-lit="true"]');
    await expect(lit).toHaveCount(0);
    await page.evaluate(() => {
      const r = document
        .querySelector(".lp-manifesto")!
        .getBoundingClientRect();
      window.scrollBy(0, r.top - window.innerHeight * 0.6);
    });
    await expect.poll(() => lit.count()).toBeGreaterThan(0);
    await page.evaluate(() => {
      const r = document
        .querySelector(".lp-manifesto")!
        .getBoundingClientRect();
      window.scrollBy(0, r.top - window.innerHeight * 0.05);
    });
    await expect
      .poll(() => lit.count())
      .toBe(await page.locator(".lp-word").count());
  });

  test("fluid layout never scrolls horizontally", async ({ page }) => {
    for (const path of ["/", "/team", "/privacy", "/terms"]) {
      await page.goto(path);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
    }
  });

  test("footer links reach team, privacy and terms pages", async ({ page }) => {
    await page.goto("/");
    for (const [name, heading] of [
      ["Meet our team", "Meet our team"],
      ["Privacy policy", "Privacy policy"],
      ["Terms and conditions", "Terms and conditions"],
    ]) {
      await page.goto("/");
      await page
        .locator(".lp-footer-links")
        .getByRole("link", { name })
        .click();
      await expect(page.getByRole("heading", { level: 1 })).toHaveText(heading);
    }
  });
});
