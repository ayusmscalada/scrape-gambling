/**
 * Shuffle.com Puppeteer worker
 */
module.exports = {
    siteKey: 'shuffle',
    siteName: 'Shuffle',
    siteUrl: 'https://shuffle.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
