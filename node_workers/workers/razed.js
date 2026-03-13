/**
 * Razed.com Puppeteer worker
 */
module.exports = {
    siteKey: 'razed',
    siteName: 'Razed',
    siteUrl: 'https://www.razed.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
