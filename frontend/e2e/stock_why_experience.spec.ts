import { test, expect } from '@playwright/test';

async function ensureInDashboard(page: any) {
  await page.goto('/');
  if (await page.locator('text=Your Money, in Perspective').isVisible({ timeout: 3000 }).catch(() => false)) {
    return;
  }
  const viewBtn = page.locator('button:has-text("View My Portfolio"), button:has-text("My Portfolio")').first();
  if (await viewBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await viewBtn.click();
    await expect(page.locator('text=Your Money, in Perspective')).toBeVisible({ timeout: 15000 });
    return;
  }

  const demoBtn = page.locator('button:has-text("Try as Demo Investor"), button:has-text("Continue as Demo")').first();
  if (await demoBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await demoBtn.click();
  } else {
    const buildBtn = page.locator('button:has-text("Build a Portfolio"), button:has-text("Get Started")').first();
    if (await buildBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await buildBtn.click();
      const authDemo = page.locator('button:has-text("Continue as Demo"), button:has-text("Try as Demo Investor")').first();
      if (await authDemo.isVisible({ timeout: 5000 }).catch(() => false)) {
        await authDemo.click();
      }
    }
  }

  for (let i = 1; i <= 5; i++) {
    await expect(page.locator(`text=Step ${i} of 6`)).toBeVisible({ timeout: 15000 });
    await page.click('button:has-text("Continue →"), button:has-text("Continue")');
  }
  await expect(page.locator('text=Step 6 of 6')).toBeVisible({ timeout: 15000 });
  await page.click('button:has-text("Generate My Portfolio")');
  await expect(page.locator('text=Your Money, in Perspective')).toBeVisible({ timeout: 35000 });
}

test.describe('Stock-Specific "Ask AI Why?" & Two-Level Parameter Explanations', () => {
  test.setTimeout(60000);

  test('Fully functional 10-section equity research analysis modal opens from holdings card', async ({ page }) => {
    await ensureInDashboard(page);

    // Expand the first holding row to reveal action buttons
    const holdingRow = page.locator('tbody tr.cursor-pointer').first();
    await expect(holdingRow).toBeVisible({ timeout: 15000 });
    await holdingRow.click();

    // Click "Ask AI why {Stock}"
    const askWhyBtn = page.locator('button:has-text("Ask AI why")').first();
    await expect(askWhyBtn).toBeVisible({ timeout: 10000 });
    await askWhyBtn.click();

    // Verify StockWhyModal is visible
    const modal = page.locator('text=SEBI Fiduciary Equity Research');
    await expect(modal).toBeVisible({ timeout: 15000 });

    // Verify 10 analytical sections exist
    await expect(page.locator('text=Strategic Selection Rationale & Portfolio Role')).toBeVisible();
    await expect(page.locator('text=Audited Fundamental Parameters (Level 1 Summary & Level 2 Deep Dive)')).toBeVisible();
    await expect(page.locator('text=Valuation Multiple Corridor')).toBeVisible();
    await expect(page.locator('text=Market & Sector Dynamics')).toBeVisible();
    await expect(page.locator('text=Macro Climate & Verified Filings')).toBeVisible();
    await expect(page.locator('text=Risk Profile & Downside Containment')).toBeVisible();
    await expect(page.locator('text=Why This Allocation? Whole-Share Mathematical Audit')).toBeVisible();
    await expect(page.locator('text=Multi-Agent Committee Deliberation Log')).toBeVisible();
    await expect(page.locator('text=Thesis Invalidation Criteria')).toBeVisible();
    await expect(page.locator('text=Final Fiduciary Conclusion')).toBeVisible();

    // Test Two-Level Parameter Expansion in Section 2
    const expandBtn = page.locator('button:has-text("Expand Level 2 Deep Dive Analysis")').first();
    await expect(expandBtn).toBeVisible();
    await expandBtn.click();

    // Verify Level 2 details expand
    await expect(page.locator('text=Formula & Methodology:').first()).toBeVisible();
    await expect(page.locator('text=Benchmark Comparison:').first()).toBeVisible();
    await expect(page.locator('text=Limitations & Analytical Caveats:').first()).toBeVisible();

    // Test Whole-Share Math in Section 7
    await expect(page.locator('text=Exact Mathematical Proof:').first()).toBeVisible();
    await expect(page.locator('text=Why not higher?').first()).toBeVisible();
    await expect(page.locator('text=Why not lower?').first()).toBeVisible();

    // Test Interactive Follow-Up Chat
    const chatInput = page.locator('input[placeholder*="Ask anything specific to"]').first();
    await expect(chatInput).toBeVisible();
    await chatInput.fill('Why this allocation?');
    await page.locator('form button[type="submit"]').click();

    // Verify Copilot response appears
    await expect(page.locator('text=Lucid Equity Research Copilot')).toBeVisible({ timeout: 15000 });

    // Close the modal
    await page.click('button:has-text("Close Research Report")');
    await expect(page.locator('text=SEBI Fiduciary Equity Research')).not.toBeVisible({ timeout: 5000 });
  });

  test('Explainability View provides Two-Level deep dive parameters and launches stock research', async ({ page }) => {
    await ensureInDashboard(page);

    // Switch to "Why This Portfolio?" tab
    await page.click('button:has-text("Why This Portfolio?")');
    await expect(page.locator('text=MULTI-AGENT AI EXPLAINABILITY & AUDIT TRAIL')).toBeVisible({ timeout: 10000 });

    // Verify the parameter table has expandable indicators
    const firstMetricRow = page.locator('table tr.cursor-pointer').first();
    await expect(firstMetricRow).toBeVisible({ timeout: 10000 });
    await firstMetricRow.click();

    // Verify Level 2 deep dive expands in Explainability view
    await expect(page.locator('text=Level 2 Deep Dive:').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Industry & Fiduciary Context:').first()).toBeVisible();

    // Click "Ask AI why" from Explainability stock card
    const askWhyBtn = page.locator('button:has-text("Ask AI why")').first();
    await expect(askWhyBtn).toBeVisible({ timeout: 5000 });
    await askWhyBtn.click();

    // Verify StockWhyModal opens
    await expect(page.locator('text=SEBI Fiduciary Equity Research')).toBeVisible({ timeout: 10000 });
    await page.click('button[aria-label="Close modal"]');
    await expect(page.locator('text=SEBI Fiduciary Equity Research')).not.toBeVisible({ timeout: 5000 });
  });

});
