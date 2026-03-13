const { sleep } = require('../utils');

/**
 * Duelbits.com Puppeteer worker
 */
module.exports = {
    siteKey: 'duelbits',
    siteName: 'Duelbits',
    siteUrl: 'https://duelbits.com/en',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
