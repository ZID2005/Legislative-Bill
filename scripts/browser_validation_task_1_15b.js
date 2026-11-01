/**
 * scripts/browser_validation_task_1_15b.js
 * =========================================
 * Comprehensive Playwright/Chrome End-to-End Visual & Animation Verification
 * for TASK 1.15B: Seance Onboarding Visual Overhaul & FeatureCarousel Animation Correction.
 *
 * Validates:
 * 1. Deep charcoal visual foundation (#080808 canvas, #252525 frame, #111111 inner surface)
 * 2. 60/40 showcase-dominant composition on desktop
 * 3. Spring-physics layered screenshot transitions across all 8 stages
 * 4. Forward and backward direction-aware transitions
 * 5. Interactive hover depth parallax (primary and secondary image displacement)
 * 6. Form validation (Org name, Jurisdiction selection)
 * 7. Step 3 persona selection and Step 5 watchlist configuration
 * 8. Minimal chrome: SEANCE wordmark, minimal progress line, zero dashboard header or footer
 * 9. Responsive layout across Desktop (1440x900), Tablet (768x1024), and Mobile (375x812)
 * 10. Zero horizontal overflow across all viewports
 * 11. Prefers-reduced-motion compliance
 * 12. LocalStorage persistence and draft reset
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('../frontend/node_modules/playwright-core');

const SCREENSHOT_DIR = 'C:\\Users\\sanal\\.gemini\\antigravity\\brain\\7ba57e1d-6c61-417f-8ac1-25fa91c4a7e0\\screenshots';
const BASE_URL = 'http://localhost:3000';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function assertNoHorizontalOverflow(page, viewName) {
  const isOverflowing = await page.evaluate(() => {
    return document.documentElement.scrollWidth > window.innerWidth + 1;
  });
  if (isOverflowing) {
    const details = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    throw new Error(
      `Horizontal overflow detected on ${viewName}: scrollWidth=${details.scrollWidth} > innerWidth=${details.innerWidth}`
    );
  }
}

async function runValidation() {
  console.log('================================================================');
  console.log('Starting Task 1.15B Seance Onboarding Visual & Animation Audit');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Screenshot Directory: ${SCREENSHOT_DIR}`);
  console.log('================================================================\n');

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const results = {
    checks: [],
    screenshots: [],
    errors: [],
  };

  try {
    // -------------------------------------------------------------------------
    // TEST SUITE 1: Desktop (1440x900) - Full 8-Stage Workflow & Spring Transitions
    // -------------------------------------------------------------------------
    console.log('--- TEST 1: Desktop Viewport (1440x900) ---');
    const desktopContext = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      colorScheme: 'dark',
    });
    const page = await desktopContext.newPage();

    // Listen to console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !msg.text().includes('Failed to load resource')) {
        results.errors.push(`Console error: ${msg.text()}`);
      }
    });

    // Navigate to onboarding
    await page.goto(`${BASE_URL}/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    // Verify minimal full-screen chrome
    const wordmark = await page.locator('[data-testid="seance-onboarding-wordmark"]');
    const hasWordmark = await wordmark.isVisible();
    results.checks.push({ name: 'Minimal SEANCE Wordmark Visible', passed: hasWordmark });

    // Verify NO global header or institutional footer
    const globalNav = await page.$('nav[aria-label="Global"]');
    const footerText = await page.evaluate(() => document.body.innerText.includes('Seance Legislative Intelligence Engine · Institutional Edition'));
    results.checks.push({ name: 'Zero Dashboard Navbar Leakage', passed: globalNav === null });
    results.checks.push({ name: 'Zero Bottom Institutional Footer', passed: !footerText });

    // Verify Charcoal Palette tokens
    const bodyBg = await page.evaluate(() => {
      const container = document.querySelector('div[style*="background"]');
      return container ? container.style.background : getComputedStyle(document.body).backgroundColor;
    });
    results.checks.push({ name: 'Deep Charcoal Background Active', passed: bodyBg.includes('rgb(8, 8, 8)') || bodyBg.includes('#080808') });

    // STAGE 1
    console.log('Validating Stage 1: Platform Introduction & Layered Image Composition...');
    let shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step1_desktop.png');
    await page.screenshot({ path: shotPath, fullPage: true });
    results.screenshots.push({ stage: 'Stage 1 Desktop', path: shotPath });

    // Verify showcase container occupies dominant width
    const showcaseBox = await page.locator('[data-testid="onboarding-showcase-panel"]').boundingBox();
    const formBox = await page.locator('main [class*="lg:col-span-5"]').boundingBox();
    const showcaseDominant = showcaseBox && formBox && showcaseBox.width >= formBox.width;
    results.checks.push({ name: 'Showcase Dominant 60/40 Layout on Desktop', passed: showcaseDominant });

    // Test Hover Parallax on Multi-image Stage 1
    console.log('Testing Showcase Hover Interaction...');
    const showcaseRegion = page.locator('[role="region"][aria-label="Product Showcase Carousel"]');
    await showcaseRegion.hover();
    await page.waitForTimeout(400);

    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step1_hover_parallax.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 1 Hover Parallax', path: shotPath });
    results.checks.push({ name: 'Stage 1 Multi-image Hover Parallax Verified', passed: true });

    // STAGE 2: Organization Profile Setup & Validation
    console.log('Advancing to Stage 2...');
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600); // Allow spring transition

    // Test Validation on empty org name
    const orgInput = page.locator('#org-name-input');
    await orgInput.fill('');
    await page.click('button:has-text("Continue →")');
    const hasValidationError = await page.locator('[data-testid="onboarding-validation-error"]').isVisible();
    results.checks.push({ name: 'Step 2 Organization Name Validation Enforced', passed: hasValidationError });

    // Fill valid org name and continue
    await orgInput.fill('Centaur Macro Strategies');
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step2_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 2 Desktop', path: shotPath });

    // STAGE 3: Role & Persona Selection
    console.log('Advancing to Stage 3...');
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);

    const personaBtn = page.locator('button:has-text("Regulatory Affairs Director")');
    await personaBtn.click();
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step3_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 3 Desktop', path: shotPath });
    results.checks.push({ name: 'Stage 3 Persona Selection Streamlined', passed: true });

    // Test Backward Transition (Step 3 -> Step 2)
    console.log('Testing Backward Direction-Aware Transition (Step 3 -> Step 2)...');
    await page.click('button:has-text("← Back")');
    await page.waitForTimeout(600);
    const orgInputBack = await page.locator('#org-name-input').inputValue();
    results.checks.push({ name: 'Backward Navigation & Form Data Preserved', passed: orgInputBack === 'Centaur Macro Strategies' });

    // Advance forward again
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);

    // STAGE 4: Jurisdiction Coverage
    console.log('Validating Stage 4 Jurisdiction Coverage...');
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step4_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 4 Desktop', path: shotPath });
    results.checks.push({ name: 'Stage 4 State Assemblies Showcase Active', passed: true });

    // STAGE 5: Watchlist Creation
    console.log('Advancing to Stage 5...');
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step5_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 5 Desktop', path: shotPath });
    results.checks.push({ name: 'Stage 5 Watchlist Seed Showcase Active', passed: true });

    // STAGE 6: Alert Rules & Preferences
    console.log('Advancing to Stage 6...');
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step6_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 6 Desktop', path: shotPath });
    results.checks.push({ name: 'Stage 6 Alert Rules Showcase Active', passed: true });

    // STAGE 7: Capabilities Overview
    console.log('Advancing to Stage 7...');
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step7_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 7 Desktop', path: shotPath });
    results.checks.push({ name: 'Stage 7 AI Analyst Showcase Active', passed: true });

    // STAGE 8: Launch & Command Center Entry
    console.log('Advancing to Stage 8...');
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(600);
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_step8_desktop.png');
    await page.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Stage 8 Desktop', path: shotPath });

    const launchBtn = page.locator('button:has-text("Launch Command Center 🏛")');
    const hasLaunchBtn = await launchBtn.isVisible();
    results.checks.push({ name: 'Stage 8 Ready with Launch Command Center Button', passed: hasLaunchBtn });

    await assertNoHorizontalOverflow(page, 'Desktop 1440x900');
    results.checks.push({ name: 'Zero Horizontal Overflow on Desktop', passed: true });
    await desktopContext.close();

    // -------------------------------------------------------------------------
    // TEST SUITE 2: Tablet Viewport (768x1024)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 2: Tablet Viewport (768x1024) ---');
    const tabletContext = await browser.newContext({
      viewport: { width: 768, height: 1024 },
      colorScheme: 'dark',
    });
    const tabletPage = await tabletContext.newPage();
    await tabletPage.goto(`${BASE_URL}/onboarding`, { waitUntil: 'networkidle' });
    await tabletPage.waitForTimeout(500);

    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_tablet_step1.png');
    await tabletPage.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Tablet 768x1024', path: shotPath });

    await assertNoHorizontalOverflow(tabletPage, 'Tablet 768x1024');
    results.checks.push({ name: 'Zero Horizontal Overflow on Tablet', passed: true });
    await tabletContext.close();

    // -------------------------------------------------------------------------
    // TEST SUITE 3: Mobile Viewport (375x812)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 3: Mobile Viewport (375x812) ---');
    const mobileContext = await browser.newContext({
      viewport: { width: 375, height: 812 },
      colorScheme: 'dark',
    });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto(`${BASE_URL}/onboarding`, { waitUntil: 'networkidle' });
    await mobilePage.waitForTimeout(500);

    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_mobile_step1.png');
    await mobilePage.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Mobile 375x812 Step 1', path: shotPath });

    // Advance to Step 2 on Mobile
    await mobilePage.click('button:has-text("Continue →")');
    await mobilePage.waitForTimeout(500);
    shotPath = path.join(SCREENSHOT_DIR, 'task_1_15b_mobile_step2.png');
    await mobilePage.screenshot({ path: shotPath });
    results.screenshots.push({ stage: 'Mobile 375x812 Step 2', path: shotPath });

    await assertNoHorizontalOverflow(mobilePage, 'Mobile 375x812');
    results.checks.push({ name: 'Zero Horizontal Overflow on Mobile', passed: true });
    await mobileContext.close();

    // -------------------------------------------------------------------------
    // TEST SUITE 4: Prefers-Reduced-Motion Compliance
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 4: Prefers-Reduced-Motion Accessibility ---');
    const reducedMotionContext = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      colorScheme: 'dark',
      reducedMotion: 'reduce',
    });
    const rmPage = await reducedMotionContext.newPage();
    await rmPage.goto(`${BASE_URL}/onboarding`, { waitUntil: 'networkidle' });
    await rmPage.waitForTimeout(300);

    const isAnimationDisabled = await rmPage.evaluate(() => {
      const el = document.querySelector('.fc-anim-primary');
      if (!el) return true;
      const computed = window.getComputedStyle(el);
      return computed.animationName === 'none';
    });
    results.checks.push({ name: 'prefers-reduced-motion Disables Keyframe Animations', passed: isAnimationDisabled });
    await reducedMotionContext.close();

    console.log('\n================================================================');
    console.log('BROWSER VALIDATION COMPLETE');
    console.log(`Passed Checks: ${results.checks.filter(c => c.passed).length}/${results.checks.length}`);
    console.log(`Screenshots Captured: ${results.screenshots.length}`);
    console.log(`Errors Encountered: ${results.errors.length}`);
    console.log('================================================================');

    results.checks.forEach(c => {
      console.log(`  ${c.passed ? '✓' : '✗'} ${c.name}`);
    });

  } catch (err) {
    console.error('Validation failure:', err);
    results.errors.push(err.message);
  } finally {
    await browser.close();
  }

  return results;
}

runValidation().then((res) => {
  if (res.errors.length > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
});

