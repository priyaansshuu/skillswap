import { expect, test } from "@playwright/test";
import path from "node:path";

test("public homepage renders real members and matches the approved viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1469, height: 1071 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Learn something new. Share what you know.",
    }),
  ).toBeVisible();
  await expect(page.locator(".provider-card")).toHaveCount(3);
  await page.evaluate(() => document.fonts.ready);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: path.resolve("../v2/.impeccable/review/hero-repro.png"),
    animations: "disabled",
  });
  await page.getByRole("link", { name: "Explore all skills" }).click();
  await expect(
    page.getByRole("heading", { name: "Find your learning partner" }),
  ).toBeVisible();
  await expect(page.locator(".provider-card").first()).toBeVisible();
});
