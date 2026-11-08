import { test, expect } from '@playwright/test';

async function ensureOnboardingChooser(page: any) {
  test.setTimeout(60000);
  await page.goto('/');

  // If already at onboarding chooser
  if (await page.locator("text=Let's understand your investment goals").isVisible({ timeout: 2000 }).catch(() => false)) {
    return;
  }

  // If on dashboard, click "+ New Portfolio"
  const newPortBtn = page.locator('button:has-text("+ New Portfolio")').first();
  if (await newPortBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await newPortBtn.click();
    if (await page.locator("text=Let's understand your investment goals").isVisible({ timeout: 4000 }).catch(() => false)) {
      return;
    }
  }

  // If "Try as Demo Investor" is visible on Landing page
  const demoBtn = page.locator('button:has-text("Try as Demo Investor")').first();
  if (await demoBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await demoBtn.click();
  } else {
    // Click Get Started or Build a Portfolio
    const startBtn = page.locator('button:has-text("Build a Portfolio"), button:has-text("Get Started")').first();
    if (await startBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await startBtn.click();
      const authDemo = page.locator('button:has-text("Continue as Demo")').first();
      if (await authDemo.isVisible({ timeout: 4000 }).catch(() => false)) {
        await authDemo.click();
      }
    }
  }

  await expect(page.locator("text=Let's understand your investment goals")).toBeVisible({ timeout: 15000 });
}

test.describe('Natural-Language Investor Onboarding & Extraction E2E', () => {

  test('Module: Option B & C - Natural-Language AI Setup, Intelligent Extraction, and Guided Wizard Prefill', async ({ page }) => {
    await ensureOnboardingChooser(page);

    // 2. Verify introductory chooser cards
    await expect(page.locator("text=Let's understand your investment goals")).toBeVisible();
    await expect(page.locator('text=Choose how you would like to share your investment requirements.')).toBeVisible();

    const nlpOptionBtn = page.locator('button:has-text("Describe your goals to Lucid")').first();
    await expect(nlpOptionBtn).toBeVisible();
    await nlpOptionBtn.click();

    // 3. Verify Natural-Language AI Studio view
    await expect(page.locator("text=Tell Lucid what you're looking to achieve")).toBeVisible();
    await expect(page.locator('text=Describe your investment goals, budget, time horizon, and preferences in your own words.')).toBeVisible();

    // 4. Click an inspiration chip or enter custom text
    const samplePromptBtn = page.locator('button:has-text("Tech Professional"), button:has-text("Aggressive Compounding")').first();
    await expect(samplePromptBtn).toBeVisible();
    await samplePromptBtn.click();

    // Verify textarea has the text
    const textarea = page.locator('textarea');
    await expect(textarea).not.toHaveValue('');

    // 5. Click "Analyze My Requirements"
    const analyzeBtn = page.locator('button:has-text("Analyze My Requirements")').first();
    await expect(analyzeBtn).toBeVisible();
    await analyzeBtn.click();

    // 6. Verify Extraction Result Preview card
    await expect(page.locator('text=Profile Successfully Extracted')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('span:has-text("Investment Capital") + span')).toContainText('3,50,000');
    await expect(page.locator('span:has-text("Time Horizon") + span')).toContainText('60 Months');
    await expect(page.locator('span:has-text("Assessed Risk Tier") + span')).toContainText(/moderate/i);

    // 7. Verify Option C: "Review & Edit in Questionnaire" prefills guided wizard
    const reviewBtn = page.locator('button:has-text("Review & Edit in Questionnaire")').first();
    await expect(reviewBtn).toBeVisible();
    await reviewBtn.click();

    // Verify we are back in guided wizard at Step 1 with prefilled values
    await expect(page.locator('text=Step 1 of 6: About You')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Continue →")');

    // Step 2: Goal
    await expect(page.locator('text=Step 2 of 6: Your Financial Goal')).toBeVisible();
    await page.click('button:has-text("Continue →")');

    // Step 3: Capital & Horizon prefilled with ₹3,50,000
    await expect(page.locator('text=Step 3 of 6: Capital & Horizon')).toBeVisible();
    await expect(page.locator('button:has-text("₹3,50,000"), input[value="350000"]').first()).toBeVisible();
  });

  test('Module: Verifies Ankur custom prompt sector mapping, experience level, and UI cleanliness', async ({ page }) => {
    await ensureOnboardingChooser(page);

    // 2. Select Natural-Language AI Setup
    const nlpOptionBtn = page.locator('button:has-text("Describe your goals to Lucid")').first();
    await expect(nlpOptionBtn).toBeVisible({ timeout: 10000 });
    await nlpOptionBtn.click();

    // 3. Fill user exact prompt
    const ankurPrompt = "Hey I am Ankur, i am a 26 year old with 50,000 to invest for 2 years. I have a moderate risk appetite and a full 1-month emergency fund in bank FDs. I have no experience in mutual funds and want strong exposure to Information Technology and Banking, but please avoid Tobacco, and Betting.";
    await page.fill('textarea', ankurPrompt);

    // 4. Click Analyze My Requirements
    const analyzeBtn = page.locator('button:has-text("Analyze My Requirements")').first();
    await analyzeBtn.click();

    // 5. Verify Extraction Result Card
    await expect(page.locator('text=Profile Successfully Extracted')).toBeVisible({ timeout: 15000 });

    // Method badge must be REMOVED from UI
    await expect(page.locator('text=Method: dynamic_heuristic_nlp_extractor')).not.toBeVisible();
    await expect(page.locator('text=dynamic_heuristic_nlp_extractor')).not.toBeVisible();

    // Investment Capital & Horizon
    await expect(page.locator('span:has-text("Investment Capital") + span')).toContainText('50,000');
    await expect(page.locator('span:has-text("Time Horizon") + span')).toContainText('24 Months (2 Yrs)');

    // Experience: Beginner / Basic
    await expect(page.locator('span:has-text("Experience & Knowledge") + span')).toContainText(/beginner/i);

    // Emergency Reserve: 1 Month (Partial)
    await expect(page.locator('span:has-text("Emergency Reserve") + div')).toContainText(/1 Month|Partial/i);

    // Preferred Sectors must contain Information Technology and Financial Services
    const prefBlock = page.locator('div:has-text("Preferred Sectors")').last();
    await expect(prefBlock).toContainText('Information Technology');
    await expect(prefBlock).toContainText('Financial Services');

    // Excluded Sectors must contain Tobacco and Betting & Gambling, and NOT Information Technology
    const exclBlock = page.locator('div:has-text("Excluded Sectors")').last();
    await expect(exclBlock).toContainText('Tobacco');
    await expect(exclBlock).toContainText(/Betting/i);
    await expect(exclBlock).not.toContainText('Information Technology');
  });

});
