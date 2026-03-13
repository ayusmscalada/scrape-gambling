const { sleep } = require('../utils');

/**
 * Rollbit.com Puppeteer worker
 */
module.exports = {
    siteKey: 'rollbit',
    siteName: 'Rollbit',
    siteUrl: 'https://rollbit.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
