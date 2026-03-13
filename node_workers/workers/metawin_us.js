/**
 * MetaWin.us Puppeteer worker
 */
module.exports = {
    siteKey: 'metawin_us',
    siteName: 'MetaWin US',
    siteUrl: 'https://metawin.us',
    async bootstrap(page) {
        await page.waitForTimeout(1000);
    },
    async run(page, stopSignal) {
        while (!stopSignal.isSet) {
            await page.waitForTimeout(5000);
        }
    },
};
