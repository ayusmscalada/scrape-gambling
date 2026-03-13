const { sleep } = require('../utils');
const { isCloudflareChallenge, solveTurnstileOnPage } = require('../captchaHelper');

/**
 * Stake.com Puppeteer worker
 * Site-specific automation logic for Stake
 */
module.exports = {
    siteKey: 'stake',
    siteName: 'Stake',
    siteUrl: 'https://stake.com',
    
    /**
     * Bootstrap: handle Cloudflare "Verify you are human" challenge via 2captcha, then wait for page ready.
     */
    async bootstrap(page) {
        await sleep(2000);
        const isChallenge = await isCloudflareChallenge(page);
        if (isChallenge) {
            const solved = await solveTurnstileOnPage(page);
            if (solved) {
                await sleep(5000);
                try {
                    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 25000 }).catch(() => {});
                } catch (e) {}
            }
        }
        await sleep(1000);
    },
    
    /**
     * Main worker loop
     * Called after bootstrap
     */
    async run(page, stopSignal) {
        // TODO: Implement Stake-specific scraping
        // - Collect live bet feeds
        // - Monitor chat
        // - Collect pack openings
        // - Extract usernames
        
        while (!stopSignal.isSet) {
            await sleep(5000); // Placeholder polling interval
        }
    },
};
