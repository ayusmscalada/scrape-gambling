const { sleep } = require('../utils');

/**
 * Gamdom.com Puppeteer worker
 */
module.exports = {
    siteKey: 'gamdom',
    siteName: 'Gamdom',
    siteUrl: 'https://gamdom.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
