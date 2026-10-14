import { expect, test } from "@playwright/test";

test("search mode follows sidebar, history, clear and mobile filter changes", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1505, height: 1045 });
  await page.goto("/explore?q=React&mode=ONLINE");
  const searchMode = page.getByRole("combobox", {
    name: "Session mode",
    exact: true,
  });
  const sidebar = page.locator("aside.filters");
  await expect(searchMode).toHaveValue("ONLINE");
  await sidebar.getByLabel("Mode", { exact: true }).selectOption("IN_PERSON");
  await expect(searchMode).toHaveValue("IN_PERSON");
  await page.getByRole("button", { name: "Find a skill" }).click();
  await expect(page).toHaveURL(/mode=IN_PERSON/);
  await sidebar.getByLabel("Mode", { exact: true }).selectOption("ONLINE");
  await expect(searchMode).toHaveValue("ONLINE");
  await page.goBack();
  await expect(searchMode).toHaveValue("IN_PERSON");
  await sidebar.getByRole("button", { name: "Clear filters" }).click();
  await expect(searchMode).toHaveValue("");
  await page.getByRole("button", { name: "Find a skill" }).click();
  expect(new URL(page.url()).searchParams.has("mode")).toBe(false);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Filter skills" });
  await drawer.getByLabel("Mode", { exact: true }).selectOption("ONLINE");
  await drawer.getByRole("button", { name: "Show results" }).click();
  await expect(searchMode).toHaveValue("ONLINE");
  await page.goto("/");
  await expect(searchMode).toHaveValue("ONLINE");
});
