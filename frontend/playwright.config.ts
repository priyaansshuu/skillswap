import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 180000,
  expect: { timeout: 15000 },
  use: {
    baseURL: process.env.SKILLSWAP_FRONTEND_URL || "http://127.0.0.1:5173",
    channel: "msedge",
    headless: true,
    trace: "off",
  },
  reporter: "list",
});
