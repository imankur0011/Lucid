const fs = require('fs');
const path = require('path');
const { marked } = require('/Users/ankur/.npm/_npx/23232c69e5d221f3/node_modules/marked');
const puppeteer = require('/Users/ankur/.npm/_npx/23232c69e5d221f3/node_modules/puppeteer');

const ROOT_DIR = '/Users/ankur/Documents/MajorProject/app';
const EXPORTS_DIR = path.join(ROOT_DIR, 'docs', 'exports');

if (!fs.existsSync(EXPORTS_DIR)) {
  fs.mkdirSync(EXPORTS_DIR, { recursive: true });
}

const docs = [
  'HIGH_LEVEL_DESIGN',
  'LOW_LEVEL_DESIGN',
  'SYSTEM_ARCHITECTURE',
  'AGENT_ARCHITECTURE',
  'METHODOLOGY',
  'DATASET_USED',
  'SETUP_AND_INSTALLATION'
];

async function convertDoc(docName, browser) {
  const mdPath = path.join(ROOT_DIR, `${docName}.md`);
  if (!fs.existsSync(mdPath)) {
    console.warn(`File not found: ${mdPath}`);
    return;
  }
  const outPdf = path.join(EXPORTS_DIR, `${docName}.pdf`);
  const rootPdf = path.join(ROOT_DIR, `${docName}.pdf`);
  const mdContent = fs.readFileSync(mdPath, 'utf8');
  const htmlBody = marked.parse(mdContent);

  const fullHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Lucid — ${docName}</title>
  <style>
    @page {
      size: A4;
      margin: 20mm 15mm 20mm 15mm;
      @bottom-right {
        content: counter(page);
      }
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.55;
      color: #142A3B;
      padding: 0;
      margin: 0;
    }
    h1 {
      color: #0B192C;
      font-size: 18pt;
      border-bottom: 2px solid #1E3E62;
      padding-bottom: 6px;
      margin-top: 0;
      margin-bottom: 14px;
      page-break-after: avoid;
    }
    h2 {
      color: #1E3E62;
      font-size: 14pt;
      border-bottom: 1px solid #E2E8F0;
      padding-bottom: 4px;
      margin-top: 22px;
      margin-bottom: 10px;
      page-break-after: avoid;
    }
    h3 {
      color: #285C4D;
      font-size: 11.5pt;
      margin-top: 16px;
      margin-bottom: 8px;
      page-break-after: avoid;
    }
    h4 {
      color: #334155;
      font-size: 10.5pt;
      margin-top: 12px;
      margin-bottom: 6px;
      page-break-after: avoid;
    }
    p, ul, ol {
      margin-top: 0;
      margin-bottom: 8px;
    }
    li {
      margin-bottom: 3px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      margin-bottom: 14px;
      font-size: 8pt;
      page-break-inside: auto;
    }
    tr {
      page-break-inside: avoid;
      page-break-after: auto;
    }
    th, td {
      border: 1px solid #CBD5E1;
      padding: 5px 6px;
      text-align: left;
      word-break: break-word;
    }
    th {
      background-color: #F1F5F9;
      color: #0F172A;
      font-weight: 700;
    }
    tr:nth-child(even) {
      background-color: #F8FAFC;
    }
    code {
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
      font-size: 8.5pt;
      background: #F1F5F9;
      padding: 1.5px 3px;
      border-radius: 3px;
      color: #0F172A;
    }
    pre {
      background: #0B192C;
      color: #F8FAFC;
      padding: 10px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 8pt;
      page-break-inside: avoid;
      line-height: 1.35;
    }
    pre code {
      background: transparent;
      color: #F8FAFC;
      padding: 0;
    }
    blockquote {
      border-left: 4px solid #285C4D;
      margin: 0;
      padding-left: 12px;
      color: #4A5568;
      font-style: italic;
    }
    hr {
      border: none;
      border-top: 1px solid #E2E8F0;
      margin: 16px 0;
    }
  </style>
</head>
<body>
  ${htmlBody}
</body>
</html>`;

  const page = await browser.newPage();
  await page.setContent(fullHtml, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: outPdf,
    format: 'A4',
    margin: {
      top: '18mm',
      right: '12mm',
      bottom: '18mm',
      left: '12mm'
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="font-size: 7.5pt; color: #94A3B8; text-align: right; width: 100%; padding-right: 12mm;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>'
  });
  await page.close();

  // Also copy to root for easy user discovery
  fs.copyFileSync(outPdf, rootPdf);
  console.log(`✅ Compiled: ${docName}.pdf (${(fs.statSync(outPdf).size / 1024).toFixed(1)} KB)`);
}

async function main() {
  console.log('Launching Puppeteer to compile design suite PDFs...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  for (const doc of docs) {
    try {
      await convertDoc(doc, browser);
    } catch (e) {
      console.error(`❌ Failed to compile ${doc}:`, e);
    }
  }

  await browser.close();
  console.log('🎉 All PDFs compiled successfully into docs/exports/ and root!');
}

main().catch(err => {
  console.error('Fatal PDF compilation error:', err);
  process.exit(1);
});
