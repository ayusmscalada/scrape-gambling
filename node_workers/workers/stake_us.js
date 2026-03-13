const { sleep } = require('../utils');

/**
 * Stake.us Puppeteer worker
 */
module.exports = {
    siteKey: 'stake_us',
    siteName: 'Stake US',
    siteUrl: 'https://stake.us',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
