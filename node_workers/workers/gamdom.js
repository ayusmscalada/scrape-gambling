/**
 * Gamdom.com Puppeteer worker
 */
module.exports = {
    siteKey: 'gamdom',
    siteName: 'Gamdom',
    siteUrl: 'https://gamdom.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
