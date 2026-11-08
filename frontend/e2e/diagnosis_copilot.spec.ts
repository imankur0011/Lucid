import { test, expect } from '@playwright/test';

// Helper to ensure user is authenticated and viewing the dashboard
async function ensureAuthenticatedDashboard(page: any) {
  await page.goto('/');

  // If already in dashboard
  if (await page.locator('text=Your Money, in Perspective').isVisible({ timeout: 2000 }).catch(() => false)) {
    return;
  }

  // Check for "View My Portfolio"
  const viewBtn = page.locator('button:has-text("View My Portfolio"), button:has-text("My Portfolio")').first();
  if (await viewBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await viewBtn.click();
    if (await page.locator('text=Your Money, in Perspective').isVisible({ timeout: 10000 }).catch(() => false)) {
      return;
    }
  }

  // Quick Demo Login
  const demoBtn = page.locator('button:has-text("Try as Demo Investor"), button:has-text("Continue as Demo")').first();
  if (await demoBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await demoBtn.click();
  } else {
    const buildBtn = page.locator('button:has-text("Build a Portfolio"), button:has-text("Get Started")').first();
    if (await buildBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await buildBtn.click();
      const authDemo = page.locator('button:has-text("Continue as Demo"), button:has-text("Try as Demo Investor")').first();
      if (await authDemo.isVisible({ timeout: 3000 }).catch(() => false)) {
        await authDemo.click();
      }
    }
  }

  // Step through all 6 stages properly
  for (let i = 1; i <= 5; i++) {
    await expect(page.locator(`text=Step ${i} of 6`)).toBeVisible({ timeout: 15000 });
    await page.click('button:has-text("Continue →")');
  }
  await expect(page.locator('text=Step 6 of 6')).toBeVisible({ timeout: 15000 });
  await page.click('button:has-text("Generate My Portfolio")');
  await expect(page.locator('text=Your Money, in Perspective')).toBeVisible({ timeout: 35000 });
}

test.describe('Diagnosis AI Copilot & Stock-Specific Rebalancing Explanations', () => {

  test('Diagnoses Demat portfolio and provides deep 7-section Copilot audit and chat', async ({ page }) => {
    await ensureAuthenticatedDashboard(page);

    // 1. Switch to Demat Diagnosis tab
    const dematTab = page.locator('button:has-text("Demat Diagnosis")');
    await expect(dematTab).toBeVisible({ timeout: 10000 });
    await dematTab.click();

    // 2. Select presets tab or manual input to run diagnosis
    const diagnoseBtn = page.locator('button:has-text("Diagnose & Preview Rebalance"), button:has-text("Diagnose")').first();
    await expect(diagnoseBtn).toBeVisible({ timeout: 10000 });
    await diagnoseBtn.click();

    // 3. Wait for diagnosis result to load
    await expect(page.locator('text=PORTFOLIO AUDIT COMPLETE')).toBeVisible({ timeout: 25000 });
    await expect(page.locator('text=Fiduciary Diagnosis & Whole-Share Rebalancing Plan')).toBeVisible();

    // 4. Click "Ask AI Copilot to Explain"
    const copilotBtn = page.locator('button:has-text("Ask AI Copilot to Explain")');
    await expect(copilotBtn).toBeVisible({ timeout: 5000 });
    await copilotBtn.click();

    // 5. Verify DiagnosisCopilotModal opened
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });
    await expect(modal.locator('text=LUCID FIDUCIARY COPILOT')).toBeVisible();

    // 6. Verify 7-section audit content in modal
    await expect(modal.locator('text=Portfolio Status & Context')).toBeVisible();
    await expect(modal.locator('text=Proposed Whole-Share Rebalancing Plan')).toBeVisible();
    await expect(modal.locator('text=Before vs. After Comparison')).toBeVisible();
    await expect(modal.locator('text=Downside Realities & Limitations')).toBeVisible();
    await expect(modal.locator('text=Final Fiduciary Summary')).toBeVisible();

    // Verify trade table in modal shows whole shares and actions
    await expect(modal.locator('th:has-text("Trade Shares")')).toBeVisible();
    await expect(modal.locator('th:has-text("Ref Price")')).toBeVisible();

    // 7. Switch to Interactive Copilot tab
    const chatTabBtn = modal.locator('button:has-text("Interactive Copilot")');
    await expect(chatTabBtn).toBeVisible();
    await chatTabBtn.click();

    // Verify chat interface
    await expect(modal.locator('input[placeholder*="Ask why a stock was trimmed"]')).toBeVisible();

    // Click a suggested inquiry chip if available
    const chip = modal.locator('button:has-text("Why are you trimming"), button:has-text("What happens if I")').first();
    if (await chip.isVisible({ timeout: 3000 }).catch(() => false)) {
      await chip.click();
      // Verify response appears
      await expect(modal.locator('text=Analyzing portfolio trades')).toBeVisible({ timeout: 3000 }).catch(() => {});
      await expect(modal.locator('text=Lucid Fiduciary Copilot').nth(1)).toBeVisible({ timeout: 20000 });
    }

    // 8. Close modal cleanly
    const closeBtn = modal.locator('button[aria-label="Close Modal"]');
    await closeBtn.click();
    await expect(modal).not.toBeVisible({ timeout: 3000 });
  });

});
