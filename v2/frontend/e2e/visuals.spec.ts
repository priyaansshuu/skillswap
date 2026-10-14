import { expect, test } from "@playwright/test";
import path from "node:path";

test("desktop, phone, tablet and reference-panel layouts remain usable", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const [name, width, height] of [
    ["desktop", 1469, 1071],
    ["mobile", 390, 1000],
    ["tablet", 768, 1024],
    ["user-817", 817, 881],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await expect(page.locator(".provider-card")).toHaveCount(3);
    await page.evaluate(() => document.fonts.ready);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: path.resolve("../.impeccable/review/" + name + ".png"),
      fullPage: true,
      animations: "disabled",
    });
    if (name === "desktop")
      await page.screenshot({
        path: path.resolve("../.impeccable/review/hero-repro.png"),
        animations: "disabled",
      });
  }
  await page.setViewportSize({ width: 1505, height: 1045 });
  await page.goto("/explore?q=React&mode=ONLINE");
  await expect(page.locator(".provider-card").first()).toBeVisible();
  await page.screenshot({
    path: path.resolve("../.impeccable/review/results-desktop.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Filter skills" });
  await expect(drawer).toBeVisible();
  await drawer.getByLabel("Minimum proficiency").selectOption("3");
  await drawer.getByRole("button", { name: "Show results" }).click();
  await expect(drawer).not.toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: path.resolve("../.impeccable/review/results-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.goto("/profile");
  await expect(page).toHaveURL(/\/login\?returnTo=/);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(
    page
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("link", { name: "Log in", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.resolve("../.impeccable/review/navigation-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.getByRole("button", { name: "Close navigation" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await page.screenshot({
    path: path.resolve("../.impeccable/review/login-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  expect(errors).toEqual([]);
});
