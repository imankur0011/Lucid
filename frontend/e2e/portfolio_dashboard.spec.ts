import { test, expect } from '@playwright/test';

// Helper to ensure page is loaded directly in Dashboard view
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

  // If on Landing page or Auth screen
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

  // Step through all 6 stages properly
  for (let i = 1; i <= 5; i++) {
    await expect(page.locator(`text=Step ${i} of 6`)).toBeVisible({ timeout: 15000 });
    await page.click('button:has-text("Continue →")');
  }
  await expect(page.locator('text=Step 6 of 6')).toBeVisible({ timeout: 15000 });
  await page.click('button:has-text("Generate My Portfolio")');
  await expect(page.locator('text=Your Money, in Perspective')).toBeVisible({ timeout: 35000 });
}

test.describe.serial('Intelligent Portfolio Creator - User Journey & Modules', () => {

  test('Module 1: Landing Page renders clear value proposition, sample allocation card, and benefits', async ({ page }) => {
    await page.goto('/');

    // Verify title and header branding
    await expect(page).toHaveTitle(/Intelligent Portfolio|Lucid/i);
    await expect(page.locator('text=Lucid').first()).toBeVisible();

    // Verify headline and beginner-friendly description
    await expect(page.locator('text=Disciplined stock portfolios')).toBeVisible();
    await expect(page.locator('text=Tell us your goals and comfort with risk')).toBeVisible();

    // Verify key trust badges
    await expect(page.locator('text=Non-Custodial').first()).toBeVisible();
    await expect(page.locator('text=100% Whole Shares').first()).toBeVisible();
    await expect(page.locator('text=Transparent Investment Thesis').first()).toBeVisible();
    await expect(page.locator('text=Zerodha / Groww Export').first()).toBeVisible();

    // Verify realistic sample preview card with blue chips
    await expect(page.locator('text=REALISTIC ALLOCATION PREVIEW')).toBeVisible();
    await expect(page.getByText('RELIANCE', { exact: true })).toBeVisible();
    await expect(page.getByText('HDFCBANK', { exact: true })).toBeVisible();
    await expect(page.getByText('TCS', { exact: true })).toBeVisible();
    await expect(page.locator('text=NSE/BSE Whole Share Rule')).toBeVisible();

    // Verify 3-step explanation
    await expect(page.locator('text=Share Goals & Risk Comfort')).toBeVisible();
    await expect(page.locator('text=Intelligent Optimization')).toBeVisible();
    await expect(page.locator('text=Execute with Conviction')).toBeVisible();

    // Verify SEBI fiduciary disclaimer
    await expect(page.locator('text=SEBI (Investment Advisers) Regulations')).toBeVisible();
  });

  test('Module 2: 1-Click Demo Investor or Registration transitions into Guided Onboarding', async ({ page }) => {
    await page.goto('/');

    // Click quick demo investor button or build portfolio if already authenticated
    const demoBtn = page.locator('button:has-text("Try as Demo Investor"), button:has-text("Build a Portfolio"), button:has-text("Start Your Onboarding →")').first();
    await expect(demoBtn).toBeVisible();
    await demoBtn.click();

    // If AuthView appears, click "Continue as Demo"
    const authDemo = page.locator('button:has-text("Continue as Demo"), button:has-text("Try as Demo Investor")').first();
    if (await authDemo.isVisible({ timeout: 2000 }).catch(() => false)) {
      await authDemo.click();
    }

    // Verify Onboarding Wizard loads at Step 1: About You
    await expect(page.locator('text=Step 1 of 6: About You')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Tell us about your investment background')).toBeVisible();
    await expect(page.locator('button:has-text("Beginner")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Intermediate")').first()).toBeVisible();
  });

  test('Module 3: Guided 6-Stage Wizard progression (Stages 1 through 6)', async ({ page }) => {
    await page.goto('/');
    const demoBtn = page.locator('button:has-text("Try as Demo Investor"), button:has-text("Build a Portfolio"), button:has-text("Start Your Onboarding →")').first();
    if (await demoBtn.isVisible()) {
      await demoBtn.click();
      const authDemo = page.locator('button:has-text("Continue as Demo"), button:has-text("Try as Demo Investor")').first();
      if (await authDemo.isVisible({ timeout: 2000 }).catch(() => false)) {
        await authDemo.click();
      }
    }

    // Step 1: Select Beginner and Continue
    await expect(page.locator('text=Step 1 of 6: About You')).toBeVisible({ timeout: 10000 });
    await page.locator('button:has-text("Beginner")').first().click();
    await page.click('button:has-text("Continue →")');

    // Step 2: Financial Goals
    await expect(page.locator('text=Step 2 of 6: Your Financial Goal')).toBeVisible();
    await page.click('button:has-text("Wealth Creation")');
    await page.click('button:has-text("Continue →")');

    // Step 3: Capital & Horizon
    await expect(page.locator('text=Step 3 of 6: Capital & Horizon')).toBeVisible();
    await expect(page.locator('button:has-text("₹2,50,000")')).toBeVisible();
    await page.click('button:has-text("5 Years")');
    await page.click('button:has-text("Continue →")');

    // Step 4: Risk Assessment
    await expect(page.locator('text=Step 4 of 6: Risk Assessment')).toBeVisible();
    await expect(page.locator('text=Risk Capacity:').first()).toBeVisible();
    await expect(page.locator('text=Risk Tolerance:').first()).toBeVisible();

    // Select conservative / zero emergency fund option to verify SEBI loss-capacity constraint
    const noEmergencyBtn = page.locator('button:has-text("No emergency reserve set aside")');
    if (await noEmergencyBtn.isVisible()) {
      await noEmergencyBtn.click();
      // Verified: Must dynamically calculate as CONSERVATIVE, NEVER falsely AGGRESSIVE
      const riskPill = page.locator('[data-testid="assessed-risk-category"]');
      await expect(riskPill).toBeVisible();
      await expect(riskPill).toHaveText(/conservative/i);
    }

    await page.click('button:has-text("Continue →")');

    // Step 5: Preferences & Safety
    await expect(page.locator('text=Step 5 of 6: Preferences & Safety')).toBeVisible();
    await expect(page.locator('text=Maximum single stock weight capped at 25%')).toBeVisible();
    await page.click('button:has-text("Continue →")');

    // Step 6: Review & Confirmation
    await expect(page.locator('text=Step 6 of 6: Review & Confirm')).toBeVisible();
    await expect(page.locator('text=Investment Capital')).toBeVisible();
    await expect(page.locator('text=Investment Horizon')).toBeVisible();
    await expect(page.locator('button:has-text("Generate My Portfolio")')).toBeVisible();
  });

  test('Module 4: Portfolio Generation runs with multi-stage honest progress into Dashboard', async ({ page }) => {
    await page.goto('/');
    const demoBtn = page.locator('button:has-text("Try as Demo Investor")').first();
    if (await demoBtn.isVisible()) {
      await demoBtn.click();
    }

    // Explicit step by step navigation through Onboarding
    await expect(page.locator('text=Step 1 of 6')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Continue →")');
    await expect(page.locator('text=Step 2 of 6')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Continue →")');
    await expect(page.locator('text=Step 3 of 6')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Continue →")');
    await expect(page.locator('text=Step 4 of 6')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Continue →")');
    await expect(page.locator('text=Step 5 of 6')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Continue →")');
    await expect(page.locator('text=Step 6 of 6')).toBeVisible({ timeout: 5000 });

    // Click Generate My Portfolio
    const generateBtn = page.locator('button:has-text("Generate My Portfolio")');
    await expect(generateBtn).toBeVisible();
    await generateBtn.click();

    // Verify arrival at Streamlined Dashboard with My Portfolio results
    await expect(page.locator('text=Your Money, in Perspective')).toBeVisible({ timeout: 35000 });
    await expect(page.locator('text=Target Capital')).toBeVisible();
    await expect(page.locator('text=Cash Reserve:').first()).toBeVisible();
  });

  test('Module 5: My Portfolio tab displays whole shares, liquid cash, and broker export', async ({ page }) => {
    await page.goto('/');

    // If on landing, navigate to active portfolio or demo
    const viewPortBtn = page.locator('button:has-text("View My Portfolio"), button:has-text("My Portfolio")').first();
    if (await viewPortBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
      await viewPortBtn.click();
    } else {
      const demoBtn = page.locator('button:has-text("Try as Demo Investor")').first();
      if (await demoBtn.isVisible()) {
        await demoBtn.click();
        for (let i = 1; i <= 5; i++) {
          await expect(page.locator(`text=Step ${i} of 6`)).toBeVisible({ timeout: 5000 });
          await page.click('button:has-text("Continue →")');
        }
        await page.click('button:has-text("Generate My Portfolio")');
      }
    }

    await expect(page.locator('text=Your Money, in Perspective')).toBeVisible({ timeout: 20000 });

    // Verify Export Basket dropdown
    const exportBtn = page.locator('button:has-text("Export Basket")');
    await expect(exportBtn).toBeVisible();
    await exportBtn.click();

    await expect(page.locator('text=Download Standard CSV')).toBeVisible();
    await expect(page.locator('text=Zerodha Kite Basket CSV')).toBeVisible();
    await expect(page.locator('text=Copy Order Slip')).toBeVisible();
    await exportBtn.click(); // close dropdown

    // Verify Expand AI Thesis drawer
    const viewThesisBtn = page.locator('button:has-text("View AI Thesis")').first();
    if (await viewThesisBtn.isVisible()) {
      await viewThesisBtn.click();
      await expect(page.locator('text=Fiduciary Investment Thesis & AI Selection Rationale')).toBeVisible();
      await expect(page.locator('text=Trailing P/E')).toBeVisible();
    }

    // Verify Compare Portfolios & Versions Modal
    const compareBtn = page.locator('button:has-text("Compare")').first();
    if (await compareBtn.isVisible()) {
      await compareBtn.click();
      await expect(page.locator('text=Compare Portfolios & Versions')).toBeVisible({ timeout: 10000 });

      // Verify dropdown selectors are present
      await expect(page.locator('#compare-select-a')).toBeVisible();
      await expect(page.locator('#compare-select-b')).toBeVisible();

      // Ensure no raw UUID input textboxes exist
      await expect(page.locator('input[placeholder*="UUID"]')).not.toBeVisible();

      // Verify Close Comparison
      await page.locator('button:has-text("Close Comparison")').click();
      await expect(page.locator('text=Compare Portfolios & Versions')).not.toBeVisible();
    }
  });

  test('Module 5b: Drift & Rebalance modal opens, displays Execution Trades with rationales, Updated Portfolio Preview, and applies rebalancing', async ({ page }) => {
    await ensureInDashboard(page);

    const rebalanceBtn = page.locator('button:has-text("Drift & Rebalance")').first();
    await expect(rebalanceBtn).toBeVisible({ timeout: 10000 });
    await rebalanceBtn.click();

    // Verify modal title
    await expect(page.locator('text=Audit & Rebalance')).toBeVisible({ timeout: 15000 });

    // Verify tab 1 is visible
    await expect(page.locator('button:has-text("Execution Trades & Why")')).toBeVisible();
    await expect(page.locator('button:has-text("Updated Portfolio Preview")')).toBeVisible();

    // Verify trade filter pills
    await expect(page.locator('button:has-text("All")').first()).toBeVisible();

    // Switch to Tab 2: Updated Portfolio Preview
    await page.locator('button:has-text("Updated Portfolio Preview")').click();
    await expect(page.locator('text=Resulting Portfolio Holdings (After Rebalance)')).toBeVisible();
    await expect(page.locator('text=Post-Rebalance Sector Exposure vs. 40.0% House Ceiling')).toBeVisible();

    // Switch back to Tab 1
    await page.locator('button:has-text("Execution Trades & Why")').click();
    await expect(page.locator('text=Whole-Share Execution Orders & Rationales')).toBeVisible();

    // Click Apply Rebalance & Update Portfolio
    const applyBtn = page.locator('button:has-text("Apply Rebalance & Update Portfolio")');
    if (await applyBtn.isVisible()) {
      await applyBtn.click();
      await expect(page.locator('text=Portfolio Updated Successfully!')).toBeVisible({ timeout: 15000 });
      await expect(page.locator('button:has-text("Portfolio Updated (v#")')).toBeVisible();
    }

    // Close modal
    await page.locator('button:has-text("Close Audit")').click();
    await expect(page.locator('text=Audit & Rebalance')).not.toBeVisible();
  });

  test('Module 6: Streamlined 4 Navigation Tabs exist and switch smoothly', async ({ page }) => {
    await ensureInDashboard(page);

    // Check all 4 primary navigation tabs
    await expect(page.locator('button:has-text("My Portfolio")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Why This Portfolio?")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Stress Tests & AI")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Demat Diagnosis")').first()).toBeVisible();

    // Switch to Why This Portfolio?
    await page.click('button:has-text("Why This Portfolio?")');
    await expect(page.locator('text=Why Were These Stocks Chosen')).toBeVisible();

    // Switch to Stress Tests & AI
    await page.click('button:has-text("Stress Tests & AI")');
    await expect(page.locator('text=Stress Testing & Downside Risk Containment')).toBeVisible();
    await expect(page.locator('button:has-text("Run -20% Market Shock")')).toBeVisible();

    // Switch to Demat Diagnosis
    await page.click('button:has-text("Demat Diagnosis")');
    await expect(page.locator('text=Portfolio Diagnosis & Rebalancing Preview')).toBeVisible();
    await expect(page.locator('button:has-text("Diagnose & Preview Rebalance")')).toBeVisible();
  });

  test('Module 6b: Preset macro shocks can be executed one after another without duplicate key or load failures', async ({ page }) => {
    await ensureInDashboard(page);

    // Switch to Stress Tests & AI
    await page.click('button:has-text("Stress Tests & AI")');
    await expect(page.locator('text=Stress Testing & Downside Risk Containment')).toBeVisible();

    // 1. Run Market Shock
    const marketShockBtn = page.locator('button:has-text("Run -20% Market Shock")');
    await expect(marketShockBtn).toBeVisible();
    await marketShockBtn.click();
    await expect(page.locator('text=Severe Market Correction (-20%)').first()).toBeVisible({ timeout: 10000 });

    // 2. Run IT Sector Shock
    const itShockBtn = page.locator('button:has-text("Run -15% IT Sector Shock")');
    await expect(itShockBtn).toBeVisible();
    await itShockBtn.click();
    await expect(page.locator('text=IT Sector Headwind (-15%)').first()).toBeVisible({ timeout: 10000 });

    // 3. Re-run Market Shock immediately
    await marketShockBtn.click();
    await expect(page.locator('text=Severe Market Correction (-20%)').first()).toBeVisible({ timeout: 10000 });

    // Ensure error banner is NOT visible
    await expect(page.locator('text=Load failed')).not.toBeVisible();
  });

  test('Module 7: Conversational Assistant responds to stock rationale inquiries in plain English', async ({ page }) => {
    await ensureInDashboard(page);

    // Switch to Stress Tests & AI tab
    await page.click('button:has-text("Stress Tests & AI")');
    await expect(page.locator('text=Ask Lucid • Conversational Stress Testing')).toBeVisible();

    const input = page.locator('input[placeholder*="Ask about a stock"]');
    await expect(input).toBeVisible();
    await input.fill('Why did you recommend RELIANCE?');
    await input.press('Enter');

    // Wait for AI reply
    await expect(page.locator('text=Strategic Role:').or(page.locator('text=Enterprise Profile:')).or(page.locator('text=Fiduciary Analysis')).first()).toBeVisible({ timeout: 15000 });
  });

  test('Module 8: Demat Diagnosis runs rebalancing preview on brokerage holdings', async ({ page }) => {
    await ensureInDashboard(page);

    // Switch to Demat Diagnosis tab
    await page.click('button:has-text("Demat Diagnosis")');
    const diagnoseBtn = page.locator('button:has-text("Diagnose & Preview Rebalance")');
    await expect(diagnoseBtn).toBeVisible();
    await diagnoseBtn.click();

    // Verify integer rebalancing suggestions table
    await expect(page.locator('text=Suggested Rebalancing Actions (Integer Shares)')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Unallocated Cash:')).toBeVisible();
  });

  test('Module 9: Profile & Security modal opens from navigation', async ({ page }) => {
    await ensureInDashboard(page);

    // Click Profile button in navbar
    const profileBtn = page.locator('button:has-text("Profile")').first();
    await expect(profileBtn).toBeVisible({ timeout: 15000 });
    await profileBtn.click();

    // Verify consumer-grade modal header and tabs
    await expect(page.locator('text=Investor Profile & Account')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('button:has-text("Account Details")')).toBeVisible();
    await expect(page.locator('button:has-text("Investment Preferences")')).toBeVisible();
    await expect(page.locator('button:has-text("Security & Password")')).toBeVisible();
    await expect(page.locator('button:has-text("Connected Demat")')).toBeVisible();

    // Verify developer and technical clutter is completely eliminated
    await expect(page.locator('text=HS256 CRYPTOGRAPHIC AUTH')).toHaveCount(0);
    await expect(page.locator('text=investor@example.invalid')).toHaveCount(0);
    await expect(page.locator('text=Profile Version Audit Trail')).toHaveCount(0);

    // Test Edit Profile inline mode
    const editBtn = page.locator('button:has-text("Edit Profile")');
    if (await editBtn.isVisible()) {
      await editBtn.click();
      await expect(page.locator('button:has-text("Save Changes")')).toBeVisible();
      await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
      await page.click('button:has-text("Cancel")');
    }

    // Test Investment Preferences Tab
    await page.click('button:has-text("Investment Preferences")');
    await expect(page.locator('text=Fiduciary Suitability Profile')).toBeVisible();
    await expect(page.locator('text=Investment Experience')).toBeVisible();
    await expect(page.locator('text=Market Knowledge Level')).toBeVisible();
    await expect(page.locator('text=SEBI Regulatory & Fiduciary Guardrails Active')).toBeVisible();

    // Verify preferences cards match current user data dynamically
    await expect(page.locator('text=Investment Experience')).toBeVisible();
    await expect(page.locator('text=Market Knowledge Level')).toBeVisible();

    // Verify Edit Preferences inline functionality & dynamic updating
    const editPrefBtn = page.locator('button:has-text("Edit Preferences")');
    await expect(editPrefBtn).toBeVisible();
    await editPrefBtn.click();
    await expect(page.locator('text=Adjust Investment Preferences')).toBeVisible();
    await expect(page.locator('button:has-text("Save Preferences")')).toBeVisible();

    // Select Beginner and Basic / Beginner
    await page.locator('form button:has-text("Beginner")').first().click();
    await page.locator('form button:has-text("Basic / Beginner")').first().click();
    await page.click('button:has-text("Save Preferences")');

    // Confirm real-time update with dynamic descriptions
    await expect(page.locator('text=Investment preferences updated successfully.')).toBeVisible();
    await expect(page.locator('text=Beginner').first()).toBeVisible();
    await expect(page.locator('text=Basic / Beginner')).toBeVisible();
    await expect(page.locator('text=New to direct equities; prioritizing established large-caps and capital protection.')).toBeVisible();
    await expect(page.locator('text=Primary background in bank deposits, fixed income, or mutual fund SIPs.')).toBeVisible();

    // Test Security Tab
    await page.click('button:has-text("Security & Password")');
    await expect(page.locator('text=Contact Verification (OTP)')).toBeVisible();
    await expect(page.locator('text=Change Password')).toBeVisible();
    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible();

    // Test Connected Demat Tab
    await page.click('button:has-text("Connected Demat")');
    await expect(page.locator('text=Non-Custodial Architecture')).toBeVisible();
    await expect(page.locator('text=Zerodha Kite')).toBeVisible();

    // Close Modal cleanly
    await page.click('button:has-text("Close")');
    await expect(page.locator('text=Investor Profile & Account')).not.toBeVisible();
  });

  test('Module 10: New Portfolio button in dashboard restarts onboarding cleanly', async ({ page }) => {
    await ensureInDashboard(page);

    // Click + New Portfolio
    const newPortBtn = page.locator('button:has-text("+ New Portfolio"), button:has-text("New Portfolio")').first();
    await expect(newPortBtn).toBeVisible();
    await newPortBtn.click();

    // Verify we are back in Onboarding Wizard
    await expect(page.locator('text=Step 1 of 6: About You')).toBeVisible();
  });

});
