/**
 * Winna.com Puppeteer worker
 */
module.exports = {
    siteKey: 'winna',
    siteName: 'Winna',
    siteUrl: 'https://winna.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
