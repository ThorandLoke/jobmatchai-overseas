const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('Opening Vercel...');
  await page.goto('https://vercel.com/new');
  
  console.log('Waiting for GitHub import button...');
  await page.waitForTimeout(3000);
  
  // Take screenshot to see current state
  await page.screenshot({ path: '/Users/weili/WorkBuddy/20260329181515/vercel-step1.png' });
  console.log('Screenshot saved: vercel-step1.png');
  
  console.log('Browser is open. Please login and import the repository.');
  console.log('Repository: ThorandLoke/denmark-home-calculator');
  
  // Keep browser open for 5 minutes
  await page.waitForTimeout(300000);
  
  await browser.close();
})();
