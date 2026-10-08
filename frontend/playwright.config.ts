import { defineConfig, devices } from "@playwright/test";

const backendPython = process.env.EVALFORGE_PYTHON ?? ".venv/bin/python";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.e2e.ts",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `DATABASE_URL=sqlite:///./e2e.db JOB_MODE=sync ${backendPython} -m alembic upgrade head && DATABASE_URL=sqlite:///./e2e.db JOB_MODE=sync ${backendPython} -m app.seed && DATABASE_URL=sqlite:///./e2e.db JOB_MODE=sync ${backendPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../backend",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000/login",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
