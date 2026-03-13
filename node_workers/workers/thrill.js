/**
 * Thrill.global Puppeteer worker
 */
const { sendUsernames } = require('../usernameApiClient');

module.exports = {
    siteKey: 'thrill',
    siteName: 'Thrill',
    siteUrl: 'https://www.thrill.global/en/casino/',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
