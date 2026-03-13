const { sleep } = require('../utils');

/**
 * Thrill.global Puppeteer worker
 */
module.exports = {
    siteKey: 'thrill',
    siteName: 'Thrill',
    siteUrl: 'https://www.thrill.global/en/casino/',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
