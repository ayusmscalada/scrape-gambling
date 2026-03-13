/**
 * Duelbits.com Puppeteer worker
 */
module.exports = {
    siteKey: 'duelbits',
    siteName: 'Duelbits',
    siteUrl: 'https://duelbits.com/en',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
