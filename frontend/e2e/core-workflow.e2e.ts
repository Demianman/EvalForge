import { expect, test } from "@playwright/test";

test("sign in, run a deterministic evaluation, and inspect results", async ({ page }) => {
  await page.goto("/login");
  await page.locator('input[name="email"]').fill("demo@evalforge.dev");
  await page.locator('input[name="password"]').fill("demo1234");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await page.screenshot({ path: "../docs/screenshots/dashboard.png", fullPage: true });
  await page.getByRole("link", { name: "Run evaluation" }).click();

  await page.locator('input[name="name"]').fill(`E2E clinical extraction ${Date.now()}`);
  await page.locator('select[name="dataset_id"]').selectOption({ index: 1 });
  await page.getByRole("button", { name: "Run evaluation" }).click();

  await expect(page).toHaveURL(/\/experiments\/\d+$/);
  await expect(page.getByText("Release quality gate: Passed")).toBeVisible();
  await expect(page.getByRole("link", { name: /Patient started metformin/ })).toBeVisible();
  await page.screenshot({ path: "../docs/screenshots/evaluation-results.png", fullPage: true });
});
