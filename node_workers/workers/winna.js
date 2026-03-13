const { sleep } = require('../utils');

/**
 * Winna.com Puppeteer worker
 */
module.exports = {
    siteKey: 'winna',
    siteName: 'Winna',
    siteUrl: 'https://winna.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
