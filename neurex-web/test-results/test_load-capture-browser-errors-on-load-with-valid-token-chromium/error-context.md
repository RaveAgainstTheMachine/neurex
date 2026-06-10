# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: test_load.spec.ts >> capture browser errors on load with valid token
- Location: e2e/test_load.spec.ts:3:1

# Error details

```
TimeoutError: page.goto: Timeout 15000ms exceeded.
Call log:
  - navigating to "http://127.0.0.1:3000/", waiting until "networkidle"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('capture browser errors on load with valid token', async ({ context, page }) => {
  4  |   page.on('console', msg => {
  5  |     console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`);
  6  |   });
  7  |   
  8  |   page.on('pageerror', err => {
  9  |     console.error(`[Uncaught Page Error]: ${err.message}\nStack:\n${err.stack}`);
  10 |   });
  11 |   
  12 |   page.on('requestfailed', request => {
  13 |     console.log(`[Request Failed]: ${request.url()} - ${request.failure()?.errorText || 'unknown'}`);
  14 |   });
  15 | 
  16 |   await context.addInitScript(() => {
  17 |     window.localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJldmFsX3J1bm5lciIsImV4cCI6MTc4MDQ2OTg4OX0.IJpUXkPUEz_ndQmIxxAhAbX-wzHOAuJ8GImkM0uXXW8');
  18 |     window.localStorage.setItem('token_timestamp', Date.now().toString());
  19 |     window.localStorage.setItem('user', JSON.stringify({ id: 'eval_runner', username: 'eval_runner', role: 'admin' }));
  20 |     window.localStorage.setItem('neurex_workspace_folders', JSON.stringify(['/games/CodeProjects/AntiGravity/Neurex/neurex']));
  21 |   });
  22 | 
  23 |   console.log("Navigating to http://127.0.0.1:3000 ...");
> 24 |   await page.goto('/', { waitUntil: 'networkidle', timeout: 15000 });
     |              ^ TimeoutError: page.goto: Timeout 15000ms exceeded.
  25 |   console.log("Navigation finished.");
  26 | 
  27 |   const preloader = page.locator('#preloader');
  28 |   const className = await preloader.getAttribute('class');
  29 |   console.log("Preloader class name:", className);
  30 | 
  31 |   const rootHTML = await page.locator('#root').innerHTML();
  32 |   console.log("Root element HTML length:", rootHTML.length);
  33 | });
  34 | 
```