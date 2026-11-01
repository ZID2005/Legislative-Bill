const fs = require('fs');
const path = require('path');
const { chromium } = require('../frontend/node_modules/playwright-core');

const ASSETS_DIR = path.join(__dirname, '..', 'frontend', 'public', 'onboarding');

if (!fs.existsSync(ASSETS_DIR)) {
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

async function capture() {
  console.log('Capturing authentic Seance screenshots for Onboarding FeatureCarousel...');
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    colorScheme: 'dark',
  });

  const page = await context.newPage();

  async function preparePage(url) {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.evaluate(() => {
      localStorage.setItem('seance_theme', 'dark');
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.remove('light');
      document.documentElement.classList.add('dark');
    });
    await page.waitForTimeout(1500);
  }

  try {
    // 1. Stage 1: Legislative Bill Dossier (Main) & Statutory Mechanics (Secondary)
    console.log('Capturing Stage 1: Bill Dossier & Statutory Mechanics...');
    await preparePage('http://localhost:3000/bills/bill_01_telecom_2023');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage1_bill_dossier.png'),
      clip: { x: 40, y: 70, width: 900, height: 620 },
    });
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage1_statutory_mechanics.png'),
      clip: { x: 120, y: 220, width: 850, height: 550 },
    });

    // 2. Stage 2: Workspace Command Center & Telemetry
    console.log('Capturing Stage 2: Workspace & Organization Configuration...');
    await preparePage('http://localhost:3000/workspace');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage2_workspace_telemetry.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage2_command_center.png'),
      clip: { x: 80, y: 160, width: 880, height: 560 },
    });

    // 3. Stage 3: Corporate Exposure Matrix & Company Dossier
    console.log('Capturing Stage 3: Corporate Exposure Matrix & Securities...');
    await preparePage('http://localhost:3000/companies/INE002A01018');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage3_exposure_matrix.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });

    // 4. Stage 4: State Assemblies & Zero-Stock-Prediction Firewall
    console.log('Capturing Stage 4: State Assemblies & Statutory Firewall...');
    await preparePage('http://localhost:3000/states');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage4_state_firewall.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });

    // 5. Stage 5: Priority Regulatory Watchlists & Bill Feeds
    console.log('Capturing Stage 5: Watchlist Telemetry...');
    await preparePage('http://localhost:3000/watchlists');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage5_watchlist_seed.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });

    // 6. Stage 6: Alerts & Notification Center
    console.log('Capturing Stage 6: Regulatory Alert Rules & Digest Delivery...');
    await preparePage('http://localhost:3000/alerts');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage6_alert_rules.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });

    // 7. Stage 7: Grounded AI Analyst Terminal & Quantitative Predictions
    console.log('Capturing Stage 7: Grounded AI Analyst Terminal...');
    await preparePage('http://localhost:3000/ai-analyst');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage7_ai_analyst.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });

    // 8. Stage 8: Quantitative Predictions & Platform Overview
    console.log('Capturing Stage 8: Quantitative Prediction Terminal & Command Center Launch...');
    await preparePage('http://localhost:3000/predictions');
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'stage8_launch_overview.png'),
      clip: { x: 40, y: 70, width: 950, height: 650 },
    });

    console.log('All 9 authentic application screenshots captured successfully in frontend/public/onboarding/!');
  } catch (err) {
    console.error('Error capturing screenshots:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

capture();
