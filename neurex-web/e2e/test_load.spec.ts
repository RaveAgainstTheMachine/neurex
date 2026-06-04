import { test, expect } from '@playwright/test';

test('capture browser errors on load with valid token', async ({ context, page }) => {
  page.on('console', msg => {
    console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`);
  });
  
  page.on('pageerror', err => {
    console.error(`[Uncaught Page Error]: ${err.message}\nStack:\n${err.stack}`);
  });
  
  page.on('requestfailed', request => {
    console.log(`[Request Failed]: ${request.url()} - ${request.failure()?.errorText || 'unknown'}`);
  });

  await context.addInitScript(() => {
    window.localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJldmFsX3J1bm5lciIsImV4cCI6MTc4MDQ2OTg4OX0.IJpUXkPUEz_ndQmIxxAhAbX-wzHOAuJ8GImkM0uXXW8');
    window.localStorage.setItem('token_timestamp', Date.now().toString());
    window.localStorage.setItem('user', JSON.stringify({ id: 'eval_runner', username: 'eval_runner', role: 'admin' }));
    window.localStorage.setItem('neurex_workspace_folders', JSON.stringify(['/games/CodeProjects/AntiGravity/Neurex/neurex']));
  });

  console.log("Navigating to http://127.0.0.1:3000 ...");
  await page.goto('/', { waitUntil: 'networkidle', timeout: 15000 });
  console.log("Navigation finished.");

  const preloader = page.locator('#preloader');
  const className = await preloader.getAttribute('class');
  console.log("Preloader class name:", className);

  const rootHTML = await page.locator('#root').innerHTML();
  console.log("Root element HTML length:", rootHTML.length);
});
