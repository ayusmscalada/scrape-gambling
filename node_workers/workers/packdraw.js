/**
 * PackDraw.com Puppeteer worker
 */
module.exports = {
    siteKey: 'packdraw',
    siteName: 'PackDraw',
    siteUrl: 'https://packdraw.com/en-us/',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
