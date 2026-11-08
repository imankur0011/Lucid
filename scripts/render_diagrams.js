const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const puppeteer = require('/Users/ankur/.npm/_npx/23232c69e5d221f3/node_modules/puppeteer');

const ROOT_DIR = '/Users/ankur/Documents/MajorProject/app';
const REPORT_IMG_DIR = path.join(ROOT_DIR, 'report', 'images');

const files = [
  'SYSTEM_ARCHITECTURE',
  'COMPLETE_DATA_FLOW',
  'NSE_BSE_DATA_FLOW',
  '00_master_er_diagram'
];

async function renderDiagram(name) {
  const mmdPath = path.join(ROOT_DIR, `${name}.mmd`);
  const svgPath = path.join(ROOT_DIR, `${name}.svg`);
  const rootPdf = path.join(ROOT_DIR, `${name}.pdf`);
  const rootPng = path.join(ROOT_DIR, `${name}.png`);
  const reportPdf = path.join(REPORT_IMG_DIR, `${name}.pdf`);
  const reportPng = path.join(REPORT_IMG_DIR, `${name}.png`);

  if (!fs.existsSync(mmdPath)) {
    console.error(`Error: ${mmdPath} does not exist!`);
    return;
  }

  console.log(`\n========================================`);
  console.log(`Generating SVG for ${name}...`);
  execSync(`npx --yes @mermaid-js/mermaid-cli -i "${mmdPath}" -o "${svgPath}" -b white`, { stdio: 'inherit' });

  console.log(`Rendering PDF and PNG via Puppeteer for ${name}...`);
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  const svgContent = fs.readFileSync(svgPath, 'utf8');
  
  // Extract viewBox width and height
  const vbMatch = svgContent.match(/viewBox="([^"]+)"/);
  let vbWidth = 1200;
  let vbHeight = 1600;
  if (vbMatch) {
    const parts = vbMatch[1].trim().split(/\s+/).map(Number);
    if (parts.length === 4) {
      vbWidth = Math.ceil(parts[2]);
      vbHeight = Math.ceil(parts[3]);
    }
  }

  console.log(`  ${name} parsed viewBox: ${vbWidth} x ${vbHeight}`);

  const html = `<!DOCTYPE html>
<html>
<head>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: white; }
    #wrapper { width: ${vbWidth}px; height: ${vbHeight}px; display: block; }
    svg { width: 100% !important; height: 100% !important; max-width: none !important; }
  </style>
</head>
<body>
  <div id="wrapper">
    ${svgContent}
  </div>
</body>
</html>`;

  await page.setViewport({ width: vbWidth, height: vbHeight, deviceScaleFactor: 2 });
  await page.setContent(html, { waitUntil: 'networkidle0' });

  // Render tight PDF
  await page.pdf({
    path: rootPdf,
    width: `${vbWidth}px`,
    height: `${vbHeight}px`,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
    printBackground: true
  });

  // Render PNG
  const wrapEl = await page.$('#wrapper');
  await wrapEl.screenshot({
    path: rootPng,
    omitBackground: false
  });

  await browser.close();

  // Copy to report/images
  fs.copyFileSync(rootPdf, reportPdf);
  fs.copyFileSync(rootPng, reportPng);
  console.log(`✅ Successfully updated ${name} in root and report/images/!`);
}

async function main() {
  for (const f of files) {
    try {
      await renderDiagram(f);
    } catch (err) {
      console.error(`Error rendering ${f}:`, err);
    }
  }
}

main().catch(console.error);
