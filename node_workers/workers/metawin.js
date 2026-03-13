const { sleep } = require('../utils');

/**
 * MetaWin.com Puppeteer worker
 */
module.exports = {
    siteKey: 'metawin',
    siteName: 'MetaWin',
    siteUrl: 'https://metawin.com',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
