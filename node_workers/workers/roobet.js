const { sleep } = require('../utils');

/**
 * Roobet.com Puppeteer worker
 */
module.exports = {
    siteKey: 'roobet',
    siteName: 'Roobet',
    siteUrl: 'https://roobet.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
