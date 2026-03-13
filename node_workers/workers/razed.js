const { sleep } = require('../utils');

/**
 * Razed.com Puppeteer worker
 */
module.exports = {
    siteKey: 'razed',
    siteName: 'Razed',
    siteUrl: 'https://www.razed.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
