const puppeteer = require('/Users/ankur/.npm/_npx/23232c69e5d221f3/node_modules/puppeteer');
const path = require('path');
const fs = require('fs');

const OUT_DIR = '/Users/ankur/Documents/MajorProject/app/report/images';

async function capture() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  console.log('Navigating to http://localhost:3000...');
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle2', timeout: 30000 });

  // 1. Landing / Main Dashboard screenshot
  await page.screenshot({ path: path.join(OUT_DIR, 'ui_landing_dashboard.png') });
  console.log('Captured ui_landing_dashboard.png');

  // Try to click around or capture key areas if present
  try {
    // Scroll down for full page view
    await page.evaluate(() => window.scrollBy(0, 600));
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(OUT_DIR, 'ui_portfolio_allocation.png') });
    console.log('Captured ui_portfolio_allocation.png');
  } catch (e) {
    console.warn('Scroll capture notice:', e.message);
  }

  await browser.close();
  console.log('Screenshots complete.');
}

capture().catch(err => {
  console.error('Screenshot error:', err);
  process.exit(0);
});
