import { expect, test, type Page } from "@playwright/test";

const password = process.env.SKILLSWAP_E2E_PASSWORD;
test.skip(
  !password,
  "Use scripts/run_browser_checks.py for an isolated database.",
);
const localInput = (date: Date) =>
  new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
async function signIn(page: Page, email: string) {
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password!);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
}

test("in-person discovery preserves the mode through sign-in and availability preview", async ({
  browser,
}) => {
  const teacherContext = await browser.newContext(),
    learnerContext = await browser.newContext();
  const teacher = await teacherContext.newPage(),
    learner = await learnerContext.newPage();
  try {
    await teacher.goto("/login");
    await signIn(teacher, "teacher@example.com");
    await expect(teacher).toHaveURL(/\/dashboard$/);
    await teacher.goto("/profile");
    const start = new Date(Date.now() + 86400000),
      end = new Date(start.getTime() + 3600000);
    await teacher.getByLabel("Available from").fill(localInput(start));
    await teacher.getByLabel("Available until").fill(localInput(end));
    await teacher
      .getByLabel("Teaching mode", { exact: true })
      .selectOption("IN_PERSON");
    await teacher
      .getByRole("button", { name: "Add availability", exact: true })
      .click();
    await expect(
      teacher.getByRole("status").filter({ hasText: "Availability added" }),
    ).toBeVisible();
    await learner.goto("/explore?q=React&mode=IN_PERSON");
    const card = learner.locator(".provider-card").filter({
      has: learner.getByRole("heading", {
        name: "Demo Teacher",
        exact: true,
      }),
    });
    await expect(card.getByText("In person", { exact: true })).toBeVisible();
    await card.getByRole("link", { name: "View profile" }).click();
    await learner
      .getByRole("link", { name: "Log in to request", exact: true })
      .click();
    await signIn(learner, "learner@example.com");
    await expect(learner).toHaveURL(/\/members\//);
    await expect(
      learner.getByLabel("Session mode", { exact: true }),
    ).toHaveValue("IN_PERSON");
    await learner.getByLabel("Window starts").fill(localInput(start));
    await learner.getByLabel("Window ends").fill(localInput(end));
    await learner
      .getByRole("button", { name: "Check availability", exact: true })
      .click();
    await expect(
      learner.getByRole("heading", { name: "A time that works" }),
    ).toBeVisible();
  } finally {
    await teacherContext.close();
    await learnerContext.close();
  }
});
