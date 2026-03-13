const { sleep } = require('../utils');

/**
 * MetaWin.us Puppeteer worker
 */
module.exports = {
    siteKey: 'metawin_us',
    siteName: 'MetaWin US',
    siteUrl: 'https://metawin.us',
    async bootstrap(page) {
        await sleep(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await sleep(5000);
        }
    },
};
