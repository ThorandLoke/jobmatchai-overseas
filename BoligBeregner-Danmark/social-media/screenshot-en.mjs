import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage();

await page.goto(`file://${process.cwd()}/promo-english.html`);
await page.waitForLoadState('networkidle');

const cards = await page.locator('.image-card').all();
for (let i = 0; i < cards.length; i++) {
    await cards[i].screenshot({ path: `image-A-en.png` });
    console.log(`✓ Image A-en saved`);
    break;
}

await browser.close();
console.log('Done!');
