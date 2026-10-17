import { test, expect } from '@playwright/test';

test.describe('Intelligent Portfolio Creator - User Journey & Modules', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to local dashboard
    await page.goto('/');
  });

  test('Module 1: Dashboard loads with JWT authentication badge and navigation tabs', async ({ page }) => {
    // Verify title and header
    await expect(page).toHaveTitle(/Intelligent Portfolio/i);
    await expect(page.locator('text=Intelligent Portfolio')).toBeVisible();

    // Verify JWT status indicator
    await expect(page.locator('text=JWT Authenticated')).toBeVisible();

    // Verify all 7 navigation tabs exist
    await expect(page.locator('text=Portfolio Generator')).toBeVisible();
    await expect(page.locator('text=Allocations & Holdings')).toBeVisible();
    await expect(page.locator('text=Explainability & Citations')).toBeVisible();
    await expect(page.locator('text=Diagnosis & Rebalancing')).toBeVisible();
    await expect(page.locator('text=Stress Scenarios')).toBeVisible();
    await expect(page.locator('text=Backtest Benchmarks')).toBeVisible();
    await expect(page.locator('text=Risk Questionnaire')).toBeVisible();
  });

  test('Module 2: Portfolio Generator tab exposes capital and constraint parameters', async ({ page }) => {
    // Active by default
    await expect(page.locator('text=Configure Portfolio Parameters')).toBeVisible();

    // Verify capital preset buttons
    await expect(page.locator('button:has-text("100,000")')).toBeVisible();
    await expect(page.locator('button:has-text("250,000")')).toBeVisible();
    await expect(page.locator('button:has-text("500,000")')).toBeVisible();

    // Verify strategy prompt textarea
    const promptInput = page.locator('textarea');
    await expect(promptInput).toBeVisible();

    // Verify application-defined safety guardrail labels
    await expect(page.locator('text=Application concentration safety cap')).toBeVisible();
    await expect(page.locator('text=Application sector diversification cap')).toBeVisible();
  });

  test('Module 3: Tab switching to Risk Questionnaire renders 5-factor assessment', async ({ page }) => {
    // Switch to Questionnaire tab
    await page.click('button:has-text("Risk Questionnaire")');

    // Verify questionnaire heading
    await expect(page.locator('text=Investor Risk Assessment Questionnaire')).toBeVisible();

    // Verify submit button
    await expect(page.locator('button:has-text("Submit Risk Assessment")')).toBeVisible();
  });

  test('Module 4: Tab switching to Backtest Benchmarks displays comparative analytics', async ({ page }) => {
    // Switch to Benchmarks tab
    await page.click('button:has-text("Backtest Benchmarks")');

    // Verify benchmark analytics heading
    await expect(page.locator('text=Quantitative Strategy Backtest')).toBeVisible();

    // Verify baselines are referenced
    await expect(page.locator('text=Equal-Weight')).toBeVisible();
  });

  test('Module 5: Tab switching to Diagnosis & Rebalancing displays diagnostic tools', async ({ page }) => {
    // Switch to Diagnosis tab
    await page.click('button:has-text("Diagnosis & Rebalancing")');

    // Verify diagnostic panel
    await expect(page.locator('text=Portfolio Diagnosis & Simulated Rebalancing')).toBeVisible();
  });

  test('Module 6: Academic & regulatory disclaimer footer is rendered', async ({ page }) => {
    // Verify footer notice
    await expect(page.locator('text=Academic Research & Educational Prototype')).toBeVisible();
    await expect(page.locator('text=SEBI (Investment Advisers) Regulations')).toBeVisible();
  });

});
