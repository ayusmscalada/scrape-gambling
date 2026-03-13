/**
 * Base worker class for site-specific automation
 * Site workers can extend this for custom behavior
 */

class BaseWorker {
    constructor(siteKey, config) {
        this.siteKey = siteKey;
        this.config = config;
    }

    /**
     * Site-specific initialization
     * Override in site workers
     */
    async bootstrap(page) {
        // Default: wait a bit for page to settle
        await page.waitForTimeout(1000);
    }

    /**
     * Main worker loop
     * Override in site workers
     */
    async run(page, stopSignal) {
        // Default: keep page alive
        while (!stopSignal.stop) {
            await page.waitForTimeout(5000);
        }
    }
}

module.exports = BaseWorker;
