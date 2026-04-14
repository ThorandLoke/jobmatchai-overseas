const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('Opening Vercel...');
  await page.goto('https://vercel.com/new');
  
  // Wait for the GitHub button and click it
  console.log('Clicking Continue with GitHub...');
  await page.waitForSelector('button:has-text("Continue with GitHub")', { timeout: 10000 });
  await page.click('button:has-text("Continue with GitHub")');
  
  console.log('Waiting for GitHub login...');
  await page.waitForTimeout(5000);
  
  // Take screenshot to see current state
  await page.screenshot({ path: '/Users/weili/WorkBuddy/20260329181515/vercel-step2.png' });
  console.log('Screenshot saved: vercel-step2.png');
  
  console.log('Please complete GitHub login in the browser...');
  
  // Wait for redirect back to Vercel
  await page.waitForURL(/vercel.com/, { timeout: 120000 });
  
  console.log('Back to Vercel, looking for repository...');
  await page.waitForTimeout(3000);
  
  // Search for the repository
  await page.fill('input[placeholder*="Search"]', 'denmark-home-calculator');
  await page.waitForTimeout(2000);
  
  // Click on the repository
  await page.click('text=ThorandLoke/denmark-home-calculator');
  
  console.log('Repository selected, configuring...');
  await page.waitForTimeout(2000);
  
  // Take screenshot
  await page.screenshot({ path: '/Users/weili/WorkBuddy/20260329181515/vercel-step3.png' });
  
  // Click Deploy
  await page.click('button:has-text("Deploy")');
  
  console.log('Deploy clicked! Waiting for deployment...');
  await page.waitForTimeout(10000);
  
  await page.screenshot({ path: '/Users/weili/WorkBuddy/20260329181515/vercel-deployed.png' });
  
  // Get the deployed URL
  const url = await page.url();
  console.log('Deployed URL:', url);
  
  await browser.close();
})();
