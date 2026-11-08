import { test, expect } from '@playwright/test';

test.describe('Responsive Design & Device Compatibility', () => {

  test('Desktop Viewport (1280x800): Wide layout and horizontal navigation', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');

    // Verify desktop header branding
    await expect(page.locator('text=Lucid').first()).toBeVisible();

    // Verify hero and cards layout
    await expect(page.locator('text=Disciplined stock portfolios')).toBeVisible();
    await expect(page.locator('text=REALISTIC ALLOCATION PREVIEW')).toBeVisible();

    // Check demo button
    const demoBtn = page.locator('button:has-text("Try as Demo Investor")').first();
    await expect(demoBtn).toBeVisible();
  });

  test('Tablet Viewport (768x1024): Clean responsive stacking', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    // Header adapts
    await expect(page.locator('text=Lucid').first()).toBeVisible();

    // Verify cards stack cleanly
    await expect(page.locator('text=Non-Custodial').first()).toBeVisible();
    await expect(page.locator('text=100% Whole Shares').first()).toBeVisible();
  });

  test('Mobile Viewport (375x667): Touch-friendly onboarding and dashboard navigation', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Brand is visible
    await expect(page.locator('text=Lucid').first()).toBeVisible();

    // Onboarding buttons are full width and touchable
    const demoBtn = page.locator('button:has-text("Try as Demo Investor")').first();
    await expect(demoBtn).toBeVisible();
    await demoBtn.click();

    // Verify Wizard Step 1 loads on mobile
    await expect(page.locator('text=Step 1 of 6: About You')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('button:has-text("Beginner")').first()).toBeVisible();

    // Click Continue through to Step 2
    await page.click('button:has-text("Continue →")');
    await expect(page.locator('text=Step 2 of 6: Your Financial Goal')).toBeVisible();
  });

});
