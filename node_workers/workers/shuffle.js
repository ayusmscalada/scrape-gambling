const { sleep } = require('../utils');

/**
 * Shuffle.com Puppeteer worker
 */
module.exports = {
    siteKey: 'shuffle',
    siteName: 'Shuffle',
    siteUrl: 'https://shuffle.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
