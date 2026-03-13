/**
 * Stake.us Puppeteer worker
 */
module.exports = {
    siteKey: 'stake_us',
    siteName: 'Stake US',
    siteUrl: 'https://stake.us',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
