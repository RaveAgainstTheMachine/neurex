import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle0' });
  
  const html = await page.evaluate(() => document.body.innerHTML);
  console.log('HTML SNIPPET:', html.substring(0, 1000));
  
  await browser.close();
})();
