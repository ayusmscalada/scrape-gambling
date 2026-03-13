/**
 * Roobet.com Puppeteer worker
 */
module.exports = {
    siteKey: 'roobet',
    siteName: 'Roobet',
    siteUrl: 'https://roobet.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
