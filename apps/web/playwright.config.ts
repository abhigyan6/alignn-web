import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";

const bravePath =
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
const executablePath =
  process.env.PLAYWRIGHT_EXECUTABLE_PATH ??
  (process.platform === "darwin" && existsSync(bravePath)
    ? bravePath
    : undefined);

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  use: {
    // Isolated runs set PLAYWRIGHT_BASE_URL to match their dev server port.
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    launchOptions: executablePath ? { executablePath } : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
});
