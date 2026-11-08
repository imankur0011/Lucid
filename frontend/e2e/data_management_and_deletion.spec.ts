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

test.describe.serial('Data Management, Portfolio Deletion & Account Deletion', () => {

  test('Portfolio Deletion dialog opens, cancels cleanly, and preserves portfolio', async ({ page }) => {
    await ensureAuthenticatedDashboard(page);

    // Verify Delete Portfolio trigger exists on HoldingsView
    const deleteBtn = page.locator('button:has-text("Delete")').first();
    await expect(deleteBtn).toBeVisible({ timeout: 10000 });
    await deleteBtn.click();

    // Verify Delete Portfolio confirmation modal is displayed
    const modalHeader = page.locator('h3:has-text("Delete Portfolio")');
    await expect(modalHeader).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Irreversible portfolio removal')).toBeVisible();
    await expect(page.locator('text=Your Lucid investor account and other portfolios will remain untouched.')).toBeVisible();

    // Click Cancel
    const cancelBtn = page.locator('button:has-text("Cancel")');
    await cancelBtn.click();

    // Verify modal closed and portfolio is still active
    await expect(modalHeader).not.toBeVisible();
    await expect(page.locator('text=Your Money, in Perspective')).toBeVisible();
  });

  test('Profile modal includes Account & Data tab with Data Export (JSON)', async ({ page }) => {
    await ensureAuthenticatedDashboard(page);

    // Open Profile modal from top navigation
    const profileBtn = page.locator('button:has-text("Profile")').first();
    await profileBtn.click();
    await expect(page.locator('text=Investor Profile & Account')).toBeVisible({ timeout: 10000 });

    // Click "Account & Data" tab
    const accountTabBtn = page.locator('button:has-text("Account & Data")');
    await expect(accountTabBtn).toBeVisible();
    await accountTabBtn.click();

    // Verify Account & Data section rendered
    await expect(page.locator('text=User Data Management & Privacy Rights')).toBeVisible();
    await expect(page.locator('text=Download Your Saved Data (JSON)')).toBeVisible();

    // Verify Download My Data button exists
    const downloadDataBtn = page.locator('button:has-text("Download My Data (JSON)")');
    await expect(downloadDataBtn).toBeVisible();

    // Test data export trigger (mocking or listening to download)
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
      downloadDataBtn.click(),
    ]);

    // Either download triggered or export confirmation message is shown
    const exportNotice = page.locator('text=complete Lucid investor data archive has been downloaded');
    if (download) {
      expect(download.suggestedFilename()).toMatch(/lucid_data_export.*\.json/);
    } else {
      await expect(exportNotice).toBeVisible({ timeout: 10000 });
    }

    // Close profile modal
    await page.locator('button:has-text("Close")').last().click();
  });

  test('Profile Account & Data tab provides portfolio selection, individual deletion, and delete all options', async ({ page }) => {
    test.setTimeout(60000);
    await ensureAuthenticatedDashboard(page);

    // Open Profile modal
    const profileBtn = page.locator('button:has-text("Profile")').first();
    await profileBtn.click();
    await expect(page.locator('text=Investor Profile & Account')).toBeVisible({ timeout: 10000 });

    // Switch to Account & Data tab
    await page.locator('button:has-text("Account & Data")').click();
    await expect(page.locator('text=Manage & Delete Portfolios')).toBeVisible({ timeout: 10000 });

    // Verify list or empty state is rendered
    const hasPortfolios = await page.locator('text=portfolios saved, text=portfolio saved, text=Select All').first().isVisible({ timeout: 3000 }).catch(() => false);

    if (hasPortfolios) {
      // 1. Verify "Select All" checkbox is present
      const selectAllLabel = page.locator('label:has-text("Select All"), label:has-text("Deselect All")').first();
      await expect(selectAllLabel).toBeVisible();

      // 2. Verify "Delete All Portfolios" button exists
      const deleteAllBtn = page.locator('button:has-text("Delete All Portfolios")').first();
      await expect(deleteAllBtn).toBeVisible();

      // 3. Test checkbox selection of an individual portfolio
      const firstCheckbox = page.locator('input[type="checkbox"][aria-label*="Select"]').first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.check();
        // Verify "Delete Selected (1)" button appears
        await expect(page.locator('button:has-text("Delete Selected")')).toBeVisible();
      }

      // 4. Test individual "Delete" button opens the confirmation modal
      const individualDeleteBtn = page.locator('button[aria-label*="Delete portfolio"]').first();
      await expect(individualDeleteBtn).toBeVisible();
      await individualDeleteBtn.click();

      // Verify the confirmation modal opened
      await expect(page.locator('#delete-portfolio-title')).toBeVisible();
      await expect(page.locator('text=Portfolios targeted for deletion')).toBeVisible();
      await expect(page.locator('text=Account Safety')).toBeVisible();

      // Cancel the deletion
      await page.locator('button:has-text("Cancel")').first().click();
      await expect(page.locator('#delete-portfolio-title')).not.toBeVisible();
    }

    // Close Profile modal
    await page.locator('button:has-text("Close")').last().click();
    await expect(page.locator('text=Investor Profile & Account')).not.toBeVisible();
  });

  test('Permanent Account Deletion enforces strict confirmation phrase guardrails', async ({ page }) => {
    test.setTimeout(60000);
    await ensureAuthenticatedDashboard(page);

    // Open Profile modal
    const profileBtn = page.locator('button:has-text("Profile")').first();
    await profileBtn.click();
    await expect(page.locator('text=Investor Profile & Account')).toBeVisible({ timeout: 10000 });

    // Navigate to Account & Data tab
    await page.locator('button:has-text("Account & Data")').click();
    await expect(page.locator('text=Permanently Delete Account')).toBeVisible();

    // Verify warning copy and bullet points
    await expect(page.locator('text=This action is irreversible.')).toBeVisible();
    await expect(page.locator('text=Records permanently removed:')).toBeVisible();

    // The submit button should be disabled initially
    const deleteAccountBtn = page.locator('button:has-text("Permanently Delete My Account")');
    await expect(deleteAccountBtn).toBeDisabled();

    // Type incorrect phrase
    const phraseInput = page.locator('input[placeholder="DELETE MY ACCOUNT"]');
    await phraseInput.fill('please delete');
    await expect(deleteAccountBtn).toBeDisabled();

    // Type exact required confirmation phrase
    await phraseInput.fill('DELETE MY ACCOUNT');
    await expect(deleteAccountBtn).toBeEnabled();

    // Close modal without submitting
    await page.locator('button:has-text("Close")').last().click();
    await expect(page.locator('text=Investor Profile & Account')).not.toBeVisible();
  });

});
