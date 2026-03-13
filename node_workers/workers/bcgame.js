/**
 * BC.Game Puppeteer worker
 */
module.exports = {
    siteKey: 'bcgame',
    siteName: 'BC.Game',
    siteUrl: 'https://bc.game',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
