import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.toString()));
  
  try {
    await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle0', timeout: 10000 });
    console.log('Page loaded successfully.');
  } catch (err) {
    console.log('Timeout or goto error:', err.toString());
  }
  
  await browser.close();
})();
