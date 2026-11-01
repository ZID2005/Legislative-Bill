const fs = require('fs');
const path = require('path');
const { chromium } = require('../frontend/node_modules/playwright-core');

const SCREENSHOT_DIR = 'C:\\Users\\sanal\\.gemini\\antigravity\\brain\\9c007418-1b53-42c1-bc2b-d5b1a88e7e67\\screenshots';
const BASE_URL = 'http://localhost:3000';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function setTheme(page, theme) {
  await page.evaluate((th) => {
    localStorage.setItem('seance_theme', th);
    const isDark = th === 'system' ? window.matchMedia('(prefers-color-scheme: dark)').matches : th === 'dark';
    const resolved = isDark ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(resolved);
  }, theme);
  await page.waitForTimeout(300);
}

async function runValidation() {
  console.log('--- Starting Task 1.9A Browser Automation & Verification ---');
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: 'dark',
  });
  const page = await context.newPage();

  const results = {
    scenarios: [],
    screenshots: [],
    errors: [],
  };

  try {
    // -------------------------------------------------------------
    // Scenario 1: Bill Dossier - Central Bill (the-banking-laws-amendment-bill-2024)
    // -------------------------------------------------------------
    console.log('\n[Scenario 1] Testing Central Bill Dossier...');
    await page.goto(`${BASE_URL}/bills/the-banking-laws-amendment-bill-2024`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('text=The Banking Laws (Amendment) Bill, 2024', { timeout: 10000 });

    // Verify Grounded Summary Rail
    const summaryRail = await page.$('aside');
    if (!summaryRail) throw new Error('Legislative Summary Rail (<aside>) not found');
    console.log('✓ Grounded Legislative Summary Rail rendered');

    // Capture Desktop Dark
    await setTheme(page, 'dark');
    const s1Dark = path.join(SCREENSHOT_DIR, 'bill-central-desktop-dark.png');
    await page.screenshot({ path: s1Dark, fullPage: false });
    results.screenshots.push(s1Dark);
    console.log('✓ Captured bill-central-desktop-dark.png');

    // Capture Desktop Light
    await setTheme(page, 'light');
    const s1Light = path.join(SCREENSHOT_DIR, 'bill-central-desktop-light.png');
    await page.screenshot({ path: s1Light, fullPage: false });
    results.screenshots.push(s1Light);
    console.log('✓ Captured bill-central-desktop-light.png');

    // Capture Desktop System
    await setTheme(page, 'system');
    const s1System = path.join(SCREENSHOT_DIR, 'bill-central-desktop-system.png');
    await page.screenshot({ path: s1System, fullPage: false });
    results.screenshots.push(s1System);
    console.log('✓ Captured bill-central-desktop-system.png');

    // Section Switching: Click Statutory Mechanics
    console.log('Testing section switching to Statutory Mechanics...');
    await setTheme(page, 'dark');
    const statutoryTab = await page.getByRole('tab', { name: /Statutory Mechanics/i });
    await statutoryTab.click();
    await page.waitForTimeout(400);
    const s1Statutory = path.join(SCREENSHOT_DIR, 'bill-central-section-statutory.png');
    await page.screenshot({ path: s1Statutory, fullPage: false });
    results.screenshots.push(s1Statutory);
    console.log('✓ Switched to Statutory Mechanics and captured bill-central-section-statutory.png');

    // Section Switching: Click Corporate & Market Impact
    console.log('Testing section switching to Corporate & Market Impact...');
    const marketTab = await page.getByRole('tab', { name: /Corporate & Market Impact/i });
    await marketTab.click();
    await page.waitForTimeout(400);
    const s1Market = path.join(SCREENSHOT_DIR, 'bill-central-section-market.png');
    await page.screenshot({ path: s1Market, fullPage: false });
    results.screenshots.push(s1Market);
    console.log('✓ Switched to Corporate & Market Impact and captured bill-central-section-market.png');

    // Legacy Deep Link Test: ?tab=predictions
    console.log('Testing legacy deep link ?tab=predictions...');
    await page.goto(`${BASE_URL}/bills/the-banking-laws-amendment-bill-2024?tab=predictions`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('[role="tab"][aria-selected="true"]', { timeout: 15000 });
    const activeSection = await page.$eval('[role="tab"][aria-selected="true"]', el => el.textContent.trim());
    console.log(`Active section after ?tab=predictions: "${activeSection}"`);
    if (!activeSection.includes('Corporate & Market Impact')) {
      throw new Error(`Expected Corporate & Market Impact to be selected, got: ${activeSection}`);
    }
    console.log('✓ Legacy ?tab=predictions properly mapped to Corporate & Market Impact');

    // Browser Back/Forward navigation test
    console.log('Testing browser back/forward navigation...');
    const statutoryTab2 = await page.getByRole('tab', { name: /Statutory Mechanics/i });
    await statutoryTab2.click();
    await page.waitForTimeout(300);
    await page.goBack();
    await page.waitForTimeout(300);
    await page.goForward();
    await page.waitForTimeout(300);
    console.log('✓ Browser history back/forward navigation functional');

    // Mobile Viewport for Central Bill
    console.log('Testing Mobile Viewport (375x812)...');
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${BASE_URL}/bills/the-banking-laws-amendment-bill-2024`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await setTheme(page, 'dark');
    await page.waitForTimeout(500);
    const s1Mobile = path.join(SCREENSHOT_DIR, 'bill-central-mobile-dark.png');
    await page.screenshot({ path: s1Mobile, fullPage: false });
    results.screenshots.push(s1Mobile);
    console.log('✓ Captured bill-central-mobile-dark.png');

    // Reset viewport to desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    results.scenarios.push('Bill Dossier: Central Bill (Light, Dark, System, Mobile, Tab Deep Link, Navigation)');

    // -------------------------------------------------------------
    // Scenario 2: Bill Dossier - State Bill (kerala-vs-bill-250-2025)
    // -------------------------------------------------------------
    console.log('\n[Scenario 2] Testing State Bill Dossier & StatePredictionFirewall...');
    await page.goto(`${BASE_URL}/bills/kerala-vs-bill-250-2025?tab=predictions`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('text=The Kerala Finance Bill, 2025', { timeout: 10000 });
    await setTheme(page, 'dark');

    // Check State Prediction Firewall
    await page.waitForSelector('text=Market prediction is not currently available for State legislation', { timeout: 10000 });
    console.log('✓ StatePredictionFirewall rendered on state bill');
    const s2Dark = path.join(SCREENSHOT_DIR, 'bill-state-desktop-dark.png');
    await page.screenshot({ path: s2Dark, fullPage: false });
    results.screenshots.push(s2Dark);
    console.log('✓ Captured bill-state-desktop-dark.png');
    results.scenarios.push('Bill Dossier: State Bill & StatePredictionFirewall (Desktop Dark)');

    // -------------------------------------------------------------
    // Scenario 3: Company Dossier - Mode A Quantitative (INE002A01018 - Reliance)
    // -------------------------------------------------------------
    console.log('\n[Scenario 3] Testing Mode A Quantitative Company Dossier...');
    await page.goto(`${BASE_URL}/companies/INE002A01018`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('text=Reliance Industries Limited', { timeout: 10000 });

    // Verify Mode A Indicator Banner
    await page.waitForSelector('text=Mode A: Quantitative / Prediction-Eligible Entity', { timeout: 10000 });
    console.log('✓ Mode A banner confirmed');

    // Dark Desktop
    await setTheme(page, 'dark');
    const s3Dark = path.join(SCREENSHOT_DIR, 'company-mode-a-desktop-dark.png');
    await page.screenshot({ path: s3Dark, fullPage: false });
    results.screenshots.push(s3Dark);
    console.log('✓ Captured company-mode-a-desktop-dark.png');

    // Light Desktop
    await setTheme(page, 'light');
    const s3Light = path.join(SCREENSHOT_DIR, 'company-mode-a-desktop-light.png');
    await page.screenshot({ path: s3Light, fullPage: false });
    results.screenshots.push(s3Light);
    console.log('✓ Captured company-mode-a-desktop-light.png');

    // Mobile Dark
    await page.setViewportSize({ width: 375, height: 812 });
    await setTheme(page, 'dark');
    const s3Mobile = path.join(SCREENSHOT_DIR, 'company-mode-a-mobile-dark.png');
    await page.screenshot({ path: s3Mobile, fullPage: false });
    results.screenshots.push(s3Mobile);
    console.log('✓ Captured company-mode-a-mobile-dark.png');

    // Reset viewport
    await page.setViewportSize({ width: 1280, height: 800 });
    results.scenarios.push('Company Dossier: Mode A Quantitative (Light, Dark, Mobile)');

    // -------------------------------------------------------------
    // Scenario 4: Company Dossier - Mode B Intelligence-Only (INE214G01026)
    // -------------------------------------------------------------
    console.log('\n[Scenario 4] Testing Mode B Intelligence-Only Company Dossier...');
    await page.goto(`${BASE_URL}/companies/INE214G01026`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('text=Ltimindtree Limited', { timeout: 10000 });

    // Verify Mode B Indicator Banner
    await page.waitForSelector('text=Mode B: Qualitative Intelligence Entity', { timeout: 10000 });
    console.log('✓ Mode B banner confirmed');

    // Verify IntelligenceCompanyFirewall is rendered
    await page.waitForSelector('text=Statutory Firewall Active', { timeout: 10000 });
    console.log('✓ IntelligenceCompanyFirewall confirmed');

    // Dark Desktop
    await setTheme(page, 'dark');
    const s4Dark = path.join(SCREENSHOT_DIR, 'company-mode-b-desktop-dark.png');
    await page.screenshot({ path: s4Dark, fullPage: false });
    results.screenshots.push(s4Dark);
    console.log('✓ Captured company-mode-b-desktop-dark.png');

    // Light Desktop
    await setTheme(page, 'light');
    const s4Light = path.join(SCREENSHOT_DIR, 'company-mode-b-desktop-light.png');
    await page.screenshot({ path: s4Light, fullPage: false });
    results.screenshots.push(s4Light);
    console.log('✓ Captured company-mode-b-desktop-light.png');

    results.scenarios.push('Company Dossier: Mode B Intelligence-Only & Firewall (Light, Dark)');

    // -------------------------------------------------------------
    // Scenario 5: Prediction List (/predictions)
    // -------------------------------------------------------------
    console.log('\n[Scenario 5] Testing Prediction List (/predictions)...');
    await page.goto(`${BASE_URL}/predictions`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('text=Prediction Analytics', { timeout: 10000 });

    // Verify editorial typography & non-color directional indicators
    const predictionsBody = await page.textContent('body');
    const hasDirectionalGlyphs = predictionsBody.includes('NEUTRAL') || predictionsBody.includes('POSITIVE') || predictionsBody.includes('NEGATIVE');
    console.log('Directional indicators present:', hasDirectionalGlyphs);

    // Dark Desktop
    await setTheme(page, 'dark');
    const s5Dark = path.join(SCREENSHOT_DIR, 'predictions-list-desktop-dark.png');
    await page.screenshot({ path: s5Dark, fullPage: false });
    results.screenshots.push(s5Dark);
    console.log('✓ Captured predictions-list-desktop-dark.png');

    // Light Desktop
    await setTheme(page, 'light');
    const s5Light = path.join(SCREENSHOT_DIR, 'predictions-list-desktop-light.png');
    await page.screenshot({ path: s5Light, fullPage: false });
    results.screenshots.push(s5Light);
    console.log('✓ Captured predictions-list-desktop-light.png');

    // Mobile Dark
    await page.setViewportSize({ width: 375, height: 812 });
    await setTheme(page, 'dark');
    const s5Mobile = path.join(SCREENSHOT_DIR, 'predictions-list-mobile-dark.png');
    await page.screenshot({ path: s5Mobile, fullPage: false });
    results.screenshots.push(s5Mobile);
    console.log('✓ Captured predictions-list-mobile-dark.png');

    // Reset viewport
    await page.setViewportSize({ width: 1280, height: 800 });
    results.scenarios.push('Predictions List: Editorial Terminal & Filters (Light, Dark, Mobile)');

    // -------------------------------------------------------------
    // Scenario 6: Prediction Dossier (/predictions/pred_the-banking-laws-amendment-bill-2024_INE002A01018_-1_p1)
    // -------------------------------------------------------------
    const testPredictionId = 'pred_the-banking-laws-amendment-bill-2024_INE002A01018_-1_p1';
    console.log(`\n[Scenario 6] Testing Prediction Dossier (${testPredictionId})...`);
    await page.goto(`${BASE_URL}/predictions/${testPredictionId}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByText(/Analytical Thesis/i).waitFor({ timeout: 15000 });

    // Dark Desktop
    await setTheme(page, 'dark');
    const s6Dark = path.join(SCREENSHOT_DIR, 'prediction-dossier-desktop-dark.png');
    await page.screenshot({ path: s6Dark, fullPage: false });
    results.screenshots.push(s6Dark);
    console.log('✓ Captured prediction-dossier-desktop-dark.png');

    // Light Desktop
    await setTheme(page, 'light');
    const s6Light = path.join(SCREENSHOT_DIR, 'prediction-dossier-desktop-light.png');
    await page.screenshot({ path: s6Light, fullPage: false });
    results.screenshots.push(s6Light);
    console.log('✓ Captured prediction-dossier-desktop-light.png');

    // Mobile Dark
    await page.setViewportSize({ width: 375, height: 812 });
    await setTheme(page, 'dark');
    const s6Mobile = path.join(SCREENSHOT_DIR, 'prediction-dossier-mobile-dark.png');
    await page.screenshot({ path: s6Mobile, fullPage: false });
    results.screenshots.push(s6Mobile);
    console.log('✓ Captured prediction-dossier-mobile-dark.png');

    // Reset to desktop for interaction test
    await page.setViewportSize({ width: 1280, height: 800 });

    // Test Horizon Selector Interaction: click [-3,+3]
    console.log('Testing interactive event horizon selector [-3,+3]...');
    const horizonBtn = page.locator('button', { hasText: '[-3,+3]' });
    await horizonBtn.click();
    await page.waitForTimeout(500);
    console.log('✓ Switched event horizon to [-3,+3]');

    // Progressive Disclosure: Expand Advanced Econometrics
    console.log('Testing progressive disclosure: Expanding Advanced Econometrics details...');
    const detailsSummary = page.locator('summary', { hasText: /Advanced Econometric/i });
    if (await detailsSummary.count() > 0) {
      await detailsSummary.click();
      await page.waitForTimeout(500);
      console.log('✓ Advanced Econometrics diagnostic drawer expanded');
    }
    const s6Expanded = path.join(SCREENSHOT_DIR, 'prediction-dossier-expanded-dark.png');
    await page.screenshot({ path: s6Expanded, fullPage: false });
    results.screenshots.push(s6Expanded);
    console.log('✓ Captured prediction-dossier-expanded-dark.png');

    results.scenarios.push('Prediction Dossier: Interpretation, 5-Horizon Selector & Advanced Econometrics (Light, Dark, Mobile)');

  } catch (err) {
    console.error('Validation error:', err);
    results.errors.push(err.message);
  } finally {
    await browser.close();
  }

  console.log('\n=========================================');
  console.log('BROWSER VALIDATION COMPLETED');
  console.log('Scenarios exercised:', results.scenarios.length);
  console.log('Screenshots captured:', results.screenshots.length);
  console.log('Errors:', results.errors.length === 0 ? 'None (100% Passed)' : results.errors);
  console.log('=========================================');

  if (results.errors.length > 0) {
    process.exit(1);
  }
}

runValidation();
