/**
 * Rollbit.com Puppeteer worker
 */
module.exports = {
    siteKey: 'rollbit',
    siteName: 'Rollbit',
    siteUrl: 'https://rollbit.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
