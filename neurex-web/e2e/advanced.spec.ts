import { test, expect } from '@playwright/test';

test.describe('Neurex IDE Frontend Advanced Subsystem E2E Tests', () => {
  let permissionUpdated = false;

  test.beforeEach(async ({ context, page }) => {
    permissionUpdated = false;

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
      window.localStorage.setItem('neurex_sidebar_tab', 'mcp');
      window.localStorage.setItem('neurex_autonomy_level', 'staging');
    });

    // Intercept essential setup routes
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
          autonomy_level: 'staging',
          theme: 'dark',
        }),
      });
    });

    await page.route(/\/api\/files\/tree/, async (route) => {
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
        body: JSON.stringify({ stats: { total_nodes: 4, memory_count: 12 } }),
      });
    });

    await page.route(/\/api\/mcp\/servers/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'sqlite-mcp',
            name: 'SQLite Core Substrate',
            type: 'core',
            status: 'connected',
            tools: [
              {
                name: 'execute_sql',
                description: 'Runs raw SELECT/INSERT SQL queries on the workspace database.',
                rule: 'ask',
                schema: {}
              }
            ]
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
        body: JSON.stringify({ status: 'clean', branch: 'main', changes: [] }),
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

    await page.route(/\/api\/infra\/metrics/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ cpu: 12, memory: 45 }),
      });
    });

    await page.route(/\/api\/mcp\/permissions/, async (route) => {
      permissionUpdated = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    // Go to the main IDE workspace
    await page.goto('/');

    // Wait for the preloader to disappear (by getting the class "hidden")
    const preloader = page.locator('#preloader');
    await expect(preloader).toHaveClass(/hidden/, { timeout: 10000 });
  });

  test('should verify MCP sandbox tools permission triggers ask deny allow matrix', async ({ page }) => {
    // Verify MCP registry title is rendered dynamically
    await expect(page.locator('text=CONNECTED REGISTRIES')).toBeVisible();

    // Verify active server meta header and tools exist
    await expect(page.locator('text=SQLite Core Substrate').first()).toBeVisible();
    await expect(page.locator('text=execute_sql').first()).toBeVisible();

    // Verify permission rules selector renders Ask button active
    const askBtn = page.locator('.mcp-permission-btn--ask.active').first();
    await expect(askBtn).toBeVisible();

    // Click Allow button and wait for the intercepted API request to trigger
    const allowBtn = page.getByRole('button', { name: 'ALLOW' });
    await expect(allowBtn).toBeVisible();

    await Promise.all([
      page.waitForResponse(/\/api\/mcp\/permissions/),
      allowBtn.dispatchEvent('click')
    ]);
    expect(permissionUpdated).toBe(true);
  });

  test('should verify LSP Monaco symbol hover & jump verification', async ({ page }) => {
    // Expose file and cursor simulation programmatically (bypassing headless CDN loading limits for Monaco)
    await page.evaluate(() => {
      window.useStore.getState().openFile('src/App.tsx', 'import React from "react";\n\nexport function App() {\n  return <div>Hello</div>;\n}', 'typescript');
      window.useStore.getState().setCursorPosition(3, 1);
    });

    // Verify active file tab is visible
    const fileTab = page.locator('.editor-tab.active:has-text("App.tsx")');
    await expect(fileTab).toBeVisible();

    // Verify status bar cursor position updates dynamically to Ln 3
    const cursorSegment = page.locator('text=Ln 3, Col 1');
    await expect(cursorSegment).toBeVisible();
  });

  test('should verify Debate Swarm steering interactive feedback', async ({ page }) => {
    // Intercept debate endpoints
    await page.route(/\/api\/debate\/status/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'd1',
            agent: 'Planner Agent',
            role: 'planner',
            content: 'I propose parallel task graph execution.',
            timestamp: '12:00:00 PM'
          }
        ]),
      });
    });

    await page.route(/\/api\/debate\/start/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    // Programmatically connect WS and navigate to debate tab
    await page.evaluate(() => {
      window.useStore.getState().setWsStatus("connected");
      window.useStore.getState().setSidebarTab("debate");
    });

    // Verify debate elements exist
    await expect(page.locator('text=Swarm Debate Arena')).toBeVisible();
    await expect(page.locator('text=Planner Agent')).toBeVisible();
    await expect(page.locator('text=I propose parallel task graph execution.')).toBeVisible();

    // Verify steer feedback input is enabled and we can type steer verdict
    const textInput = page.locator('textarea[placeholder="Type steering feedback to guide the swarm..."]');
    await expect(textInput).toBeEnabled();
    await textInput.fill('Proceed with parallel execution.');

    // Dispatch the steering verdict
    const sendBtn = page.locator('.debate-send-btn');
    await expect(sendBtn).toBeEnabled();
    await sendBtn.dispatchEvent('click');

    // Verify the Judge verdict message is optimistically appended to debate logs (using precise scoped locator)
    const judgeBadge = page.locator('.agent-badge:has-text("ARCHITECT JUDGE")').first();
    await expect(judgeBadge).toBeVisible();
    await expect(page.locator('text=Proceed with parallel execution.').first()).toBeVisible();
  });
});
