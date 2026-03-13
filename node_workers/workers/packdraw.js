const { sleep } = require('../utils');

/**
 * PackDraw.com Puppeteer worker
 */
module.exports = {
    siteKey: 'packdraw',
    siteName: 'PackDraw',
    siteUrl: 'https://packdraw.com/en-us/',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
