const { sleep } = require('../utils');

/**
 * BC.Game Puppeteer worker
 */
module.exports = {
    siteKey: 'bcgame',
    siteName: 'BC.Game',
    siteUrl: 'https://bc.game',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
