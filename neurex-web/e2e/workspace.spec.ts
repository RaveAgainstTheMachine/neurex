import { test, expect } from '@playwright/test';

test.describe('Neurex IDE Frontend Workspace E2E Tests', () => {
  test.beforeEach(async ({ context, page }) => {
    // Capture all browser console messages and route them to terminal output
    page.on('console', (msg) => {
      console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`);
    });

    // Inject fake token, timestamp, user, and settings into localStorage to bypass AuthOverlay
    await context.addInitScript(() => {
      window.localStorage.setItem('token', 'fake-token');
      window.localStorage.setItem('token_timestamp', Date.now().toString());
      window.localStorage.setItem('user', JSON.stringify({ id: 'admin', username: 'admin', role: 'admin' }));
      window.localStorage.setItem('neurex_show_ai', 'true');
      window.localStorage.setItem('neurex_autonomy_level', 'limited');
    });

    // Intercept all API calls via regex matchers to ensure full trailing-slash support
    await page.route(/\/api\/auth\/onboarding\/status/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ onboarding_required: false }),
      });
    });

    await page.route(/\/api\/auth\/me/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'admin', username: 'admin', role: 'admin' }),
      });
    });

    await page.route(/\/api\/settings/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          autonomy_level: 'limited',
          theme: 'dark',
          font_size: 14,
        }),
      });
    });

    await page.route(/\/api\/observability\/trace/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'trace-1',
            agent_type: 'planner',
            action: 'Analyzing workspace structure',
            detail: 'Scanning files and directory nodes recursively',
            status: 'success',
            timestamp: new Date().toISOString(),
          },
          {
            id: 'trace-2',
            agent_type: 'researcher',
            action: 'Running grep search',
            detail: 'Query: "autonomy" in files',
            status: 'running',
            tool_used: 'grep_search',
            timestamp: new Date().toISOString(),
          }
        ]),
      });
    });

    await page.route(/\/api\/observability\/replay/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/files\/tree/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/infra\/status/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy', cpu: 12, memory: 45 }),
      });
    });

    await page.route(/\/api\/infra\/metrics/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/infra\/registry/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/infra\/engines/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/infra\/peers/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/benchmarks/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'idle',
          current_case: null,
          log: [],
          results: [],
          score: '10/12',
          percentage: 83,
          duration_s: 4.5,
          start_time: 0.0,
          error_details: null,
        }),
      });
    });

    await page.route(/\/api\/skills/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/memory/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ stats: {} }),
      });
    });

    await page.route(/\/api\/languages\/supported/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(['typescript', 'python', 'rust']),
      });
    });

    await page.route(/\/api\/git\/status/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: "clean", branch: "main", changes: [] }),
      });
    });

    await page.route(/\/api\/tasks/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/chat/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route(/\/api\/languages\/installable/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Go to the main IDE workspace
    await page.goto('/');

    // Wait for the preloader to disappear (by getting the class "hidden")
    const preloader = page.locator('#preloader');
    await expect(preloader).toHaveClass(/hidden/, { timeout: 10000 });
  });

  test('should load workspace and display layout elements', async ({ page }) => {
    // Assert the page title
    await expect(page).toHaveTitle(/Neurex/i);

    // Assert the main editor panels exist or are visible
    const bottomPanel = page.locator('.bottom-panel, #bottom-panel');
    await expect(bottomPanel).toBeVisible();
  });

  test('should toggle to Flight Log tab and show traces', async ({ page }) => {
    // Locate the FLIGHT LOG button tab and click it
    const flightLogTabButton = page.locator('button:has-text("FLIGHT LOG")');
    await expect(flightLogTabButton).toBeVisible();
    await flightLogTabButton.click();
    
    // Verify that the teleplay canvas section is rendered
    const teleplayCanvas = page.locator('.teleplay-canvas');
    await expect(teleplayCanvas).toBeVisible();
    
    // Check for canvas header
    const canvasHeader = page.locator('.teleplay-header__title');
    await expect(canvasHeader).toBeVisible();
  });

  test('should dynamically change autonomy level options', async ({ page }) => {
    // Find the autonomy selector dropdown trigger
    const selectorTrigger = page.locator('.autonomy-selector-footer .custom-select__trigger');
    await expect(selectorTrigger).toBeVisible();
    await selectorTrigger.click();

    // Select the newly supported "staging" mode button
    const stagingOption = page.locator('.custom-select__option:has-text("staging")');
    await expect(stagingOption).toBeVisible();
    await stagingOption.click();

    // Assert selector updated the display text
    await expect(selectorTrigger).toHaveText(/staging/i);
  });
});
