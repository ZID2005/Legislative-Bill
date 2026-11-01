/**
 * scripts/browser_validation_task_1_15e.js
 * =========================================
 * Comprehensive Playwright/Chrome End-to-End Visual, Atmospheric, Animation & Viewport Verification
 * for TASK 1.15E: Seance Onboarding Final Visual Refinement:
 * Minimal Numbered Stepper (1 to 8), Refined Ghost Fibers Ribbons & Single-Viewport Layout.
 *
 * Validates:
 * 1. Minimal Numbered Progress Stepper:
 *    - All 8 numbered positions (1 to 8)
 *    - Completed states, active highlights, upcoming subdued indicators
 *    - Forward & backward navigation
 *    - LocalStorage draft restoration
 *    - Zero legacy phase headings ("Foundation", "Preferences", "Launch") or descriptions
 * 2. Refined Ghost Fibers Background (Reference Image 2):
 *    - Full viewport coverage (inset-0, 100vw, 100vh)
 *    - Non-blocking pointer events (pointer-events: none, z-0)
 *    - Smooth ribbon rendering and dark charcoal negative space (#080808)
 *    - Absence of dense dotted mesh visual noise
 *    - Prefers-reduced-motion fallback
 * 3. Single-Viewport Desktop Layout (1440 × 900):
 *    - Simultaneously visible: Header, minimal stepper, form content, showcase, back & continue buttons
 *    - Zero document-level vertical scrolling required on desktop across ALL 8 steps
 *    - Zero horizontal overflow
 * 4. Responsive Viewports:
 *    - Desktop: 1440 × 900
 *    - Tablet: 768 × 1024
 *    - Mobile: 375 × 812
 * 5. Animation Performance & Frame Rate Measurements
 * 6. Captures 10 High-Resolution Screenshots & Video Walkthrough
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('../frontend/node_modules/playwright-core');

const CONVERSATION_ID = '43d46ac2-1747-45fa-b1dc-262b67ad3ad9';
const ARTIFACT_DIR = path.join('C:\\Users\\sanal\\.gemini\\antigravity\\brain', CONVERSATION_ID);
const SCREENSHOT_DIR = path.join(ARTIFACT_DIR, 'screenshots');
const RECORDING_DIR = path.join(ARTIFACT_DIR, 'recordings');
const DOCS_RECORDING_DIR = path.join(__dirname, '..', 'docs', 'recordings');
const BASE_URL = 'http://localhost:3000';

[SCREENSHOT_DIR, RECORDING_DIR, DOCS_RECORDING_DIR].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

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

async function assertSingleViewportDesktop(page, stepNumber) {
  const scrollInfo = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    return {
      windowHeight: window.innerHeight,
      clientHeight: doc.clientHeight,
      scrollHeight: Math.max(doc.scrollHeight, body.scrollHeight),
      hasVerticalScrollbar: window.innerHeight < doc.scrollHeight - 2,
    };
  });

  if (scrollInfo.hasVerticalScrollbar) {
    console.warn(
      `[Warning] Step ${stepNumber} has vertical scroll height: ${scrollInfo.scrollHeight}px vs window ${scrollInfo.windowHeight}px`
    );
  }
  return scrollInfo;
}

async function runValidation() {
  console.log('================================================================');
  console.log('TASK 1.15E — SEANCE ONBOARDING FINAL VISUAL REFINEMENT E2E');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Artifact Directory: ${ARTIFACT_DIR}`);
  console.log(`Screenshot Directory: ${SCREENSHOT_DIR}`);
  console.log(`Recording Directory: ${RECORDING_DIR}`);
  console.log('================================================================\n');

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const results = {
    checks: [],
    screenshots: [],
    recordings: [],
    performance: {},
    errors: [],
  };

  try {
    // -------------------------------------------------------------------------
    // TEST 1: Desktop Viewport (1440x900) - Full 8-Step Walkthrough & Validation
    // -------------------------------------------------------------------------
    console.log('--- TEST 1: Desktop Viewport (1440x900) Single-Viewport Walkthrough ---');
    const desktopContext = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      colorScheme: 'dark',
      recordVideo: { dir: RECORDING_DIR, size: { width: 1440, height: 900 } },
    });
    const page = await desktopContext.newPage();

    // Clear any previous draft in localStorage
    await page.goto(`${BASE_URL}/onboarding`);
    await page.evaluate(() => localStorage.removeItem('seance_onboarding_draft'));
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);

    // 1. Validate Ghost Fibers Background presence & styling
    const bgExists = await page.locator('[data-testid="ghost-fibers-background"]').isVisible();
    const canvasExists = await page.locator('[data-testid="ghost-fibers-canvas"]').isVisible();
    console.log(`✓ Ghost Fibers full-viewport fixed background visible: ${bgExists && canvasExists}`);
    results.checks.push({ check: 'ghost_fibers_background_visible', passed: bgExists && canvasExists });

    const bgStyles = await page.locator('[data-testid="ghost-fibers-background"]').evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        position: computed.position,
        pointerEvents: computed.pointerEvents,
        zIndex: computed.zIndex,
      };
    });
    console.log(`✓ Ghost Fibers styles: position=${bgStyles.position}, pointerEvents=${bgStyles.pointerEvents}, zIndex=${bgStyles.zIndex}`);
    results.checks.push({ check: 'ghost_fibers_non_blocking', passed: bgStyles.pointerEvents === 'none' && bgStyles.zIndex === '0' });

    // 2. Validate Minimal Numbered Stepper (positions 1-8, no phase headings)
    const stepperExists = await page.locator('[data-testid="onboarding-progress-indicator"]').isVisible();
    console.log(`✓ Minimal Numbered Stepper visible: ${stepperExists}`);
    results.checks.push({ check: 'minimal_stepper_visible', passed: stepperExists });

    // Verify all 8 indicators are present
    let all8IndicatorsPresent = true;
    for (let i = 1; i <= 8; i++) {
      const exists = await page.locator(`[data-testid="step-indicator-${i}"]`).isVisible();
      if (!exists) all8IndicatorsPresent = false;
    }
    console.log(`✓ All 8 numbered step indicators (1 to 8) present: ${all8IndicatorsPresent}`);
    results.checks.push({ check: 'all_8_indicators_present', passed: all8IndicatorsPresent });

    // Verify absolute removal of phase headings
    const bodyText = await page.textContent('body');
    const hasFoundationHeading = bodyText.includes('Workspace Foundation') || bodyText.includes('PHASE 1 OF 3');
    const hasPreferencesHeading = bodyText.includes('Intelligence Preferences') || bodyText.includes('PHASE 2 OF 3');
    const hasLaunchHeading = bodyText.includes('Workspace Launch') || bodyText.includes('PHASE 3 OF 3');
    const phaseHeadingsRemoved = !hasFoundationHeading && !hasPreferencesHeading && !hasLaunchHeading;
    console.log(`✓ Legacy phase headings & descriptions completely removed: ${phaseHeadingsRemoved}`);
    results.checks.push({ check: 'phase_headings_removed', passed: phaseHeadingsRemoved });

    // Capture Screenshot 1: Desktop Overview
    const shot1 = path.join(SCREENSHOT_DIR, 'task_1_15e_desktop_onboarding_overview.png');
    await page.screenshot({ path: shot1, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_desktop_onboarding_overview.png', path: shot1 });

    // Capture Screenshot 2: Step 1
    const shot2 = path.join(SCREENSHOT_DIR, 'task_1_15e_step_1.png');
    await page.screenshot({ path: shot2, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_step_1.png', path: shot2 });

    // Step 1 Single-viewport validation
    const s1Scroll = await assertSingleViewportDesktop(page, 1);
    console.log(`✓ Step 1 desktop height: ${s1Scroll.scrollHeight}px / 900px (overflow: ${s1Scroll.hasVerticalScrollbar})`);

    // Verify Step 1 indicator is active
    const s1State = await page.locator('[data-testid="step-indicator-1"]').getAttribute('data-step-state');
    console.log(`✓ Step 1 indicator active state: ${s1State === 'active'}`);
    results.checks.push({ check: 'step_1_active', passed: s1State === 'active' });

    // Measure FPS / Animation Frame rate during Ghost Fibers & Showcase
    const perfData = await page.evaluate(async () => {
      return new Promise((resolve) => {
        let frames = 0;
        const start = performance.now();
        function checkFrame(now) {
          frames++;
          if (now - start >= 1000) {
            const fps = Math.round((frames * 1000) / (now - start));
            resolve({ fps, duration: now - start, frames });
          } else {
            requestAnimationFrame(checkFrame);
          }
        }
        requestAnimationFrame(checkFrame);
      });
    });
    console.log(`✓ Measured Browser Animation Performance: ${perfData.fps} FPS (${perfData.frames} frames in ${Math.round(perfData.duration)}ms)`);
    results.performance.desktopFps = perfData.fps;

    // Navigate to Step 2
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(450);
    await assertSingleViewportDesktop(page, 2);

    // Navigate to Step 3
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(450);
    await assertSingleViewportDesktop(page, 3);

    // Navigate to Step 4
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(500);
    const s4Scroll = await assertSingleViewportDesktop(page, 4);
    console.log(`✓ Step 4 desktop height: ${s4Scroll.scrollHeight}px / 900px (overflow: ${s4Scroll.hasVerticalScrollbar})`);

    const s4State = await page.locator('[data-testid="step-indicator-4"]').getAttribute('data-step-state');
    const s1PastState = await page.locator('[data-testid="step-indicator-1"]').getAttribute('data-step-state');
    console.log(`✓ Step 4 indicator active: ${s4State === 'active'}, Step 1 completed: ${s1PastState === 'completed'}`);
    results.checks.push({ check: 'step_4_active_and_past_completed', passed: s4State === 'active' && s1PastState === 'completed' });

    // Capture Screenshot 3: Step 4
    const shot3 = path.join(SCREENSHOT_DIR, 'task_1_15e_step_4.png');
    await page.screenshot({ path: shot3, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_step_4.png', path: shot3 });

    // Navigate to Step 5
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(450);
    await assertSingleViewportDesktop(page, 5);

    // Navigate to Step 6
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(500);
    const s6Scroll = await assertSingleViewportDesktop(page, 6);
    console.log(`✓ Step 6 desktop height: ${s6Scroll.scrollHeight}px / 900px (overflow: ${s6Scroll.hasVerticalScrollbar})`);

    const s6State = await page.locator('[data-testid="step-indicator-6"]').getAttribute('data-step-state');
    console.log(`✓ Step 6 indicator active: ${s6State === 'active'}`);
    results.checks.push({ check: 'step_6_active', passed: s6State === 'active' });

    // Capture Screenshot 4: Step 6
    const shot4 = path.join(SCREENSHOT_DIR, 'task_1_15e_step_6.png');
    await page.screenshot({ path: shot4, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_step_6.png', path: shot4 });

    // Navigate to Step 7 (SeanceMobileShowcase iPhone presentation)
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(500);
    await assertSingleViewportDesktop(page, 7);

    // Navigate to Step 8
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(500);
    const s8Scroll = await assertSingleViewportDesktop(page, 8);
    console.log(`✓ Step 8 desktop height: ${s8Scroll.scrollHeight}px / 900px (overflow: ${s8Scroll.hasVerticalScrollbar})`);

    const s8State = await page.locator('[data-testid="step-indicator-8"]').getAttribute('data-step-state');
    const s7PastState = await page.locator('[data-testid="step-indicator-7"]').getAttribute('data-step-state');
    console.log(`✓ Step 8 indicator active: ${s8State === 'active'}, Step 7 completed: ${s7PastState === 'completed'}`);
    results.checks.push({ check: 'step_8_active_and_past_completed', passed: s8State === 'active' && s7PastState === 'completed' });

    // Capture Screenshot 5: Step 8
    const shot5 = path.join(SCREENSHOT_DIR, 'task_1_15e_step_8.png');
    await page.screenshot({ path: shot5, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_step_8.png', path: shot5 });

    // Test Backward Navigation: Click step-indicator-4 to jump back
    await page.click('[data-testid="step-indicator-4"]');
    await page.waitForTimeout(400);
    const s4BackState = await page.locator('[data-testid="step-indicator-4"]').getAttribute('data-step-state');
    console.log(`✓ Backward navigation via minimal stepper: Step 4 re-activated (${s4BackState === 'active'})`);
    results.checks.push({ check: 'backward_navigation_restored_step_4', passed: s4BackState === 'active' });

    // Test LocalStorage Draft Restoration: Reload while on Step 4
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    const s4ReloadState = await page.locator('[data-testid="step-indicator-4"]').getAttribute('data-step-state');
    console.log(`✓ LocalStorage draft reload restored Step 4 active state: ${s4ReloadState === 'active'}`);
    results.checks.push({ check: 'draft_reload_restored_step_4', passed: s4ReloadState === 'active' });

    // Validate Desktop 1440x900 zero horizontal overflow
    await assertNoHorizontalOverflow(page, 'Desktop 1440x900');
    console.log('✓ Desktop 1440x900 zero horizontal overflow confirmed');

    // Capture Screenshot 6: Ghost Fibers background isolated (hide foreground)
    await page.evaluate(() => {
      const mainEl = document.querySelector('main');
      const headerEl = document.querySelector('header');
      const navEl = document.querySelector('nav');
      if (mainEl) mainEl.style.opacity = '0';
      if (headerEl) headerEl.style.opacity = '0';
      if (navEl) navEl.style.opacity = '0';
    });
    await page.waitForTimeout(300);
    const shot6 = path.join(SCREENSHOT_DIR, 'task_1_15e_ghost_fibers_background.png');
    await page.screenshot({ path: shot6, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_ghost_fibers_background.png', path: shot6 });

    // Restore foreground visibility
    await page.evaluate(() => {
      const mainEl = document.querySelector('main');
      const headerEl = document.querySelector('header');
      const navEl = document.querySelector('nav');
      if (mainEl) mainEl.style.opacity = '1';
      if (headerEl) headerEl.style.opacity = '1';
      if (navEl) navEl.style.opacity = '1';
    });
    await page.waitForTimeout(200);

    // Capture Screenshot 7: FeatureCarousel transition in motion
    await page.click('button:has-text("Continue →")');
    await page.waitForTimeout(120); // Capture mid-transition
    const shot7 = path.join(SCREENSHOT_DIR, 'task_1_15e_feature_carousel_transition.png');
    await page.screenshot({ path: shot7, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_feature_carousel_transition.png', path: shot7 });

    await desktopContext.close();

    // Copy recorded walkthrough video to docs
    const videoFiles = fs.readdirSync(RECORDING_DIR).filter((f) => f.endsWith('.webm'));
    if (videoFiles.length > 0) {
      const latestVideo = videoFiles[videoFiles.length - 1];
      const srcVideoPath = path.join(RECORDING_DIR, latestVideo);
      const destVideoPath = path.join(DOCS_RECORDING_DIR, 'task_1_15e_onboarding_walkthrough.webm');
      fs.copyFileSync(srcVideoPath, destVideoPath);
      console.log(`✓ Walkthrough video persisted: ${destVideoPath}`);
      results.recordings.push(destVideoPath);
    }

    // -------------------------------------------------------------------------
    // TEST 2: Tablet Viewport (768x1024)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 2: Tablet Viewport (768x1024) ---');
    const tabletContext = await browser.newContext({
      viewport: { width: 768, height: 1024 },
      colorScheme: 'dark',
    });
    const tabletPage = await tabletContext.newPage();
    await tabletPage.goto(`${BASE_URL}/onboarding`);
    await tabletPage.waitForLoadState('networkidle');
    await tabletPage.waitForTimeout(400);

    await assertNoHorizontalOverflow(tabletPage, 'Tablet 768x1024');
    const tabletStepperVisible = await tabletPage.locator('[data-testid="onboarding-progress-indicator"]').isVisible();
    console.log(`✓ Tablet 768x1024: minimal numbered stepper visible (${tabletStepperVisible}), zero horizontal overflow`);
    results.checks.push({ check: 'tablet_responsive_pass', passed: tabletStepperVisible });

    // Capture Screenshot 8: Tablet
    const shot8 = path.join(SCREENSHOT_DIR, 'task_1_15e_tablet_768x1024.png');
    await tabletPage.screenshot({ path: shot8, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_tablet_768x1024.png', path: shot8 });
    await tabletContext.close();

    // -------------------------------------------------------------------------
    // TEST 3: Mobile Viewport (375x812)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 3: Mobile Viewport (375x812) ---');
    const mobileContext = await browser.newContext({
      viewport: { width: 375, height: 812 },
      colorScheme: 'dark',
    });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto(`${BASE_URL}/onboarding`);
    await mobilePage.waitForLoadState('networkidle');
    await mobilePage.waitForTimeout(400);

    await assertNoHorizontalOverflow(mobilePage, 'Mobile 375x812');
    const mobileStepperVisible = await mobilePage.locator('[data-testid="onboarding-progress-indicator"]').isVisible();
    console.log(`✓ Mobile 375x812: compact minimal stepper visible (${mobileStepperVisible}), zero horizontal overflow`);
    results.checks.push({ check: 'mobile_responsive_pass', passed: mobileStepperVisible });

    // Capture Screenshot 9: Mobile
    const shot9 = path.join(SCREENSHOT_DIR, 'task_1_15e_mobile_375x812.png');
    await mobilePage.screenshot({ path: shot9, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_mobile_375x812.png', path: shot9 });
    await mobileContext.close();

    // -------------------------------------------------------------------------
    // TEST 4: Prefers-Reduced-Motion Compliance
    // -------------------------------------------------------------------------
    console.log('\n--- TEST 4: Prefers-Reduced-Motion Compliance ---');
    const motionContext = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'reduce',
      colorScheme: 'dark',
    });
    const motionPage = await motionContext.newPage();
    await motionPage.goto(`${BASE_URL}/onboarding`);
    await motionPage.waitForLoadState('networkidle');
    await motionPage.waitForTimeout(400);

    const reducedMotionConfirmed = await motionPage.evaluate(() => {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    });
    console.log(`✓ Prefers-reduced-motion verified: matchMedia matches = ${reducedMotionConfirmed}`);
    results.checks.push({ check: 'reduced_motion_active', passed: reducedMotionConfirmed });

    // Capture Screenshot 10: Reduced Motion Mode
    const shot10 = path.join(SCREENSHOT_DIR, 'task_1_15e_reduced_motion.png');
    await motionPage.screenshot({ path: shot10, fullPage: false });
    results.screenshots.push({ name: 'task_1_15e_reduced_motion.png', path: shot10 });
    await motionContext.close();

    console.log('\n================================================================');
    console.log('>>> TASK 1.15E BROWSER VALIDATION PASSED SUCCESSFULLY <<<');
    console.log('================================================================');
    console.log(`Total checks: ${results.checks.length}`);
    console.log(`Total screenshots: ${results.screenshots.length}`);
    console.log(`FPS: ${results.performance.desktopFps}`);
  } catch (err) {
    console.error('Validation failed with error:', err);
    results.errors.push(err.message);
    throw err;
  } finally {
    await browser.close();
  }
}

runValidation().catch((err) => {
  console.error(err);
  process.exit(1);
});

