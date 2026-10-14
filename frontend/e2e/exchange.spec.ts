import { expect, test, type Page } from "@playwright/test";
import crypto from "node:crypto";
import path from "node:path";

const password = process.env.SKILLSWAP_E2E_PASSWORD;
test.skip(
  !password,
  "Run scripts/run_browser_checks.py for an isolated PostgreSQL browser demo.",
);
function localInput(date: Date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}
async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password!);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}
async function addSkill(page: Page, kind: string, skill: string) {
  const panel = page
    .locator("section")
    .filter({ has: page.getByRole("heading", { name: kind, exact: true }) });
  await panel.getByRole("combobox").first().selectOption({ label: skill });
  await panel.getByRole("button", { name: "Add skill", exact: true }).click();
  await expect(
    panel.getByText(skill + " · Level", { exact: false }),
  ).toBeVisible();
}

test("one-account teaching and learning completes a real dual-confirmed exchange", async ({
  browser,
}) => {
  test.setTimeout(300000);
  const teacherContext = await browser.newContext(),
    learnerContext = await browser.newContext();
  const teacher = await teacherContext.newPage(),
    learner = await learnerContext.newPage();
  const errors: string[] = [];
  for (const page of [teacher, learner])
    page.on("pageerror", (error) => errors.push(error.message));
  try {
    await login(teacher, "blank01@example.com");
    await teacher.goto("/profile");
    await teacher
      .getByLabel("Name", { exact: true })
      .fill("UI Teaching Member");
    await teacher
      .getByLabel("About you", { exact: true })
      .fill("I share React and also want to learn Mathematics.");
    await teacher.getByRole("button", { name: "Save profile" }).click();
    await expect(
      teacher.getByRole("status").filter({ hasText: "Saved successfully" }),
    ).toBeVisible();
    await addSkill(teacher, "Skills I can teach", "React");
    await addSkill(teacher, "Skills I want to learn", "Mathematics");
    await login(learner, "blank02@example.com");
    await learner.goto("/profile");
    await learner
      .getByLabel("Name", { exact: true })
      .fill("UI Learning Member");
    await learner.getByRole("button", { name: "Save profile" }).click();
    await addSkill(learner, "Skills I can teach", "Mathematics");
    await addSkill(learner, "Skills I want to learn", "React");

    const start = new Date(Math.ceil((Date.now() + 20000) / 60000) * 60000);
    const end = new Date(start.getTime() + 600000);
    await teacher.getByLabel("Available from").fill(localInput(start));
    await teacher.getByLabel("Available until").fill(localInput(end));
    await teacher
      .getByRole("button", { name: "Add availability", exact: true })
      .click();
    await expect(
      teacher.getByRole("status").filter({ hasText: "Availability added" }),
    ).toBeVisible();

    await learner.goto("/explore?q=React&mode=ONLINE");
    const card = learner.locator(".provider-card").filter({
      has: learner.getByRole("heading", {
        name: "UI Teaching Member",
        exact: true,
      }),
    });
    await expect(card).toBeVisible();
    await card.getByRole("link", { name: "View profile" }).click();
    await learner.getByLabel("Duration in minutes").fill("2");
    await learner.getByLabel("Window starts").fill(localInput(start));
    await learner.getByLabel("Window ends").fill(localInput(end));
    await learner
      .getByRole("button", { name: "Check availability", exact: true })
      .click();
    await expect(
      learner.getByRole("heading", { name: "A time that works" }),
    ).toBeVisible();
    await learner.getByLabel("I’m happy with this suggested time.").check();
    await learner
      .getByRole("button", { name: "Send session request", exact: true })
      .click();
    await expect(learner).toHaveURL(/\/requests\//);
    const requestPath = new URL(learner.url()).pathname;
    await teacher.goto(requestPath);
    await teacher
      .getByRole("button", { name: "Accept request", exact: true })
      .click();
    await expect(teacher).toHaveURL(/\/sessions\//);
    const sessionPath = new URL(teacher.url()).pathname;
    await learner.goto("/credits");
    await expect(
      learner
        .locator(".credit-summary")
        .getByText("2 minutes", { exact: true }),
    ).toBeVisible();
    await learner.goto(sessionPath);
    await expect(
      teacher.getByRole("button", { name: "Start session", exact: true }),
    ).toBeEnabled({ timeout: 100000 });
    await teacher
      .getByRole("button", { name: "Start session", exact: true })
      .click();
    await expect(
      learner.getByRole("button", { name: "Confirm completion", exact: true }),
    ).toBeVisible();
    await expect(
      learner.getByRole("button", { name: "Confirm completion", exact: true }),
    ).toBeDisabled();
    await expect(
      learner.getByRole("button", { name: "Confirm completion", exact: true }),
    ).toBeEnabled({ timeout: 160000 });
    await learner.getByLabel("Actual minutes completed").fill("1");
    await learner
      .getByRole("button", { name: "Confirm completion", exact: true })
      .click();
    await teacher.getByLabel("Actual minutes completed").fill("2");
    await teacher
      .getByRole("button", { name: "Confirm completion", exact: true })
      .click();
    await expect(
      teacher.getByRole("status").filter({ hasText: "Your durations differ" }),
    ).toBeVisible();
    await teacher.getByLabel("Actual minutes completed").fill("1");
    await teacher
      .getByRole("button", { name: "Update my confirmation", exact: true })
      .click();
    await expect(
      teacher.getByText(
        "Both participants confirmed. 1 minute transferred exactly once.",
        { exact: true },
      ),
    ).toBeVisible();
    await expect(
      learner.getByText(
        "Both participants confirmed. 1 minute transferred exactly once.",
        { exact: true },
      ),
    ).toBeVisible();
    await teacher.screenshot({
      path: path.resolve("../v2/.impeccable/review/session-completed.png"),
      fullPage: true,
      animations: "disabled",
    });
    await learner
      .getByRole("button", { name: "Write a review", exact: true })
      .click();
    await learner
      .getByLabel("Your review", { exact: true })
      .fill("A helpful peer exchange, completed through the working UI.");
    await learner
      .getByRole("button", { name: "Post review", exact: true })
      .click();
    await expect(
      learner.getByText(
        "A helpful peer exchange, completed through the working UI.",
        { exact: true },
      ),
    ).toBeVisible();
    await learner.goto("/credits");
    await expect(
      learner
        .locator(".credit-summary")
        .getByText("119 minutes · 1 hour 59 min", { exact: true }),
    ).toHaveCount(2);
    await expect(
      learner.getByText("Minutes used learning", { exact: true }),
    ).toHaveCount(1);
    await teacher.goto("/credits");
    await expect(
      teacher
        .locator(".credit-summary")
        .getByText("121 minutes · 2 hours 1 min", { exact: true }),
    ).toHaveCount(2);
    await expect(
      teacher.getByText("Minutes earned teaching", { exact: true }),
    ).toHaveCount(1);
    await teacher.screenshot({
      path: path.resolve("../v2/.impeccable/review/credits-after-transfer.png"),
      fullPage: true,
      animations: "disabled",
    });
    expect(errors).toEqual([]);
  } finally {
    await teacherContext.close();
    await learnerContext.close();
  }
});

test("skill approval, admin permissions, logout and expiry work through the UI", async ({
  browser,
}) => {
  const memberContext = await browser.newContext(),
    adminContext = await browser.newContext();
  const member = await memberContext.newPage(),
    admin = await adminContext.newPage();
  const name = "Origami " + crypto.randomBytes(3).toString("hex");
  try {
    await login(member, "blank01@example.com");
    await member.goto("/profile");
    await member.getByLabel("Suggested skill name").fill(name);
    await member
      .getByLabel("Why would you like to add it?")
      .fill("I want to share paper folding with peers.");
    await member
      .getByRole("button", { name: "Suggest a skill", exact: true })
      .click();
    await expect(
      member
        .getByRole("status")
        .filter({ hasText: "Suggestion sent for admin review" }),
    ).toBeVisible();
    await member.goto("/admin");
    await expect(
      member.getByRole("heading", { name: "Administrator access required" }),
    ).toBeVisible();
    await login(admin, "admin@example.com");
    await admin.goto("/admin?tab=suggestions");
    const item = admin
      .locator("section.panel")
      .filter({ has: admin.getByRole("heading", { name, exact: true }) });
    await item.getByLabel("Approved category").fill("Arts");
    await item
      .getByLabel("Decision note")
      .fill("Approved for peer teaching in the catalog.");
    await item.getByRole("button", { name: "Resolve suggestion" }).click();
    await expect(item.locator(".status")).toHaveText("approved");
    await member.goto("/profile");
    const offered = member.locator("section").filter({
      has: member.getByRole("heading", {
        name: "Skills I can teach",
        exact: true,
      }),
    });
    await offered.getByRole("combobox").first().selectOption({ label: name });
    await offered
      .getByRole("button", { name: "Add skill", exact: true })
      .click();
    await expect(
      offered.getByText(name + " · Level", { exact: false }),
    ).toBeVisible();
    await admin.goto("/admin?tab=members");
    await expect(
      admin.getByRole("heading", { name: "Members", exact: true }),
    ).toBeVisible();
    await admin.goto("/admin?tab=audit");
    await expect(
      admin.getByText("RESOLVE SKILL SUGGESTION", { exact: true }),
    ).toBeVisible();
    await admin.goto("/admin?tab=evaluation");
    await expect(
      admin.getByRole("heading", { name: "Recorded outcomes" }),
    ).toBeVisible();
    await member
      .getByRole("button", { name: "Log out", exact: true })
      .first()
      .click();
    await member.goto("/credits");
    await expect(member).toHaveURL(/\/login\?returnTo=/);
    await login(member, "blank01@example.com");
    await member.evaluate(() => {
      const current = JSON.parse(sessionStorage.getItem("skillswap-session")!);
      sessionStorage.setItem(
        "skillswap-session",
        JSON.stringify({ ...current, expiresAt: 0 }),
      );
    });
    await member.reload();
    await expect(member).toHaveURL(/\/login\?returnTo=/);
  } finally {
    await memberContext.close();
    await adminContext.close();
  }
});

test("registration creates one usable member account", async ({ page }) => {
  const email =
    "browser-" + crypto.randomBytes(5).toString("hex") + "@example.com";
  await page.goto("/register");
  await page.getByLabel("Your name").fill("New Browser Member");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password!);
  await page.getByRole("button", { name: "Create my account" }).click();
  await expect(page).toHaveURL(/\/profile$/);
  await expect(
    page.getByRole("heading", { name: "Skills I can teach", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Skills I want to learn", exact: true }),
  ).toBeVisible();
  await page.goto("/credits");
  await expect(
    page
      .locator(".credit-summary")
      .getByText("120 minutes · 2 hours", { exact: true }),
  ).toHaveCount(2);
});

test("a completed-session dispute can be dismissed through the admin UI", async ({
  browser,
}) => {
  const memberContext = await browser.newContext(),
    adminContext = await browser.newContext();
  const member = await memberContext.newPage(),
    admin = await adminContext.newPage();
  try {
    await login(member, "demo4@example.com");
    await member.goto("/sessions");
    await member
      .getByRole("link", { name: "React", exact: true })
      .first()
      .click();
    const sessionPath = new URL(member.url()).pathname;
    await member
      .getByRole("button", { name: "Report a problem", exact: true })
      .click();
    await member
      .getByLabel("Describe the problem")
      .fill("Please review this recorded demonstration session.");
    await member
      .getByRole("button", { name: "Submit dispute", exact: true })
      .click();
    await expect(
      member.getByRole("heading", { name: "Awaiting administrator review" }),
    ).toBeVisible();
    await login(admin, "admin@example.com");
    await admin.goto("/admin?tab=disputes");
    const item = admin.locator("section.panel").filter({
      hasText: "Please review this recorded demonstration session.",
    });
    await item
      .getByLabel("Resolution", { exact: true })
      .selectOption("DISMISS");
    await item
      .getByLabel("Resolution note")
      .fill("Verified the demonstration record; completion remains valid.");
    await item
      .getByLabel("I confirm this resolution and any credit correction.")
      .check();
    await item
      .getByRole("button", { name: "Resolve dispute", exact: true })
      .click();
    await expect(item.locator(".status")).toHaveText("resolved");
    await member.goto(sessionPath);
    await expect(
      member.getByText(
        "Recorded completed session. 60 minutes · 1 hour transferred exactly once.",
        { exact: true },
      ),
    ).toBeVisible();
    await member.goto("/credits");
    await expect(
      member.getByText("Minutes used learning", { exact: true }),
    ).toHaveCount(1);
  } finally {
    await memberContext.close();
    await adminContext.close();
  }
});
