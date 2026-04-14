import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage();

// Load the HTML file
await page.goto(`file://${process.cwd()}/promo-images.html`);
await page.waitForLoadState('networkidle');

// Screenshot each card
const cards = await page.locator('.image-card').all();
for (let i = 0; i < cards.length; i++) {
    await cards[i].screenshot({ path: `image-${String.fromCharCode(65+i)}.png` });
    console.log(`✓ Image ${String.fromCharCode(65+i)} saved`);
}

await browser.close();
console.log('Done!');
