/**
 * MetaWin.com Puppeteer worker
 */
module.exports = {
    siteKey: 'metawin',
    siteName: 'MetaWin',
    siteUrl: 'https://metawin.com',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
