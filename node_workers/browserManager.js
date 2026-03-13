/**
 * Browser Manager for Puppeteer workers
 * Manages browser instances for each gambling platform site
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Set Puppeteer cache directory if not already set
// Use local path when running outside Docker
if (!process.env.PUPPETEER_CACHE_DIR) {
    const os = require('os');
    const isDocker = fs.existsSync('/.dockerenv');
    process.env.PUPPETEER_CACHE_DIR = isDocker 
        ? '/app/.puppeteer-cache' 
        : path.join(os.homedir(), '.cache', 'puppeteer');
}

class BrowserManager {
    constructor() {
        this.browsers = new Map(); // site_key -> { browser, page, state, config }
        // Use local profiles directory when running outside Docker
        const isDocker = fs.existsSync('/.dockerenv');
        this.profilesBaseDir = isDocker 
            ? '/app/profiles' 
            : path.join(__dirname, '..', 'profiles');
        
        // Ensure profiles directory exists
        // Note: Directory is mounted as volume, so it should exist
        // If it doesn't exist, try to create it (may fail due to permissions)
        if (!fs.existsSync(this.profilesBaseDir)) {
            try {
                fs.mkdirSync(this.profilesBaseDir, { recursive: true });
                console.log(`Created profiles directory: ${this.profilesBaseDir}`);
            } catch (e) {
                console.warn(`Could not create profiles directory (may already exist via volume mount): ${e.message}`);
            }
        }
        
        // Check if directory is accessible
        try {
            fs.accessSync(this.profilesBaseDir, fs.constants.R_OK | fs.constants.W_OK);
            console.log(`Profiles directory is accessible: ${this.profilesBaseDir}`);
        } catch (e) {
            console.error(`WARNING: Profiles directory ${this.profilesBaseDir} is not accessible: ${e.message}`);
            console.error('This may cause issues when creating browser profiles.');
            console.error('Fix: Ensure ./profiles directory on host is writable by user 1000');
        }
    }

    /**
     * Get worker state
     */
    getState(siteKey) {
        const worker = this.browsers.get(siteKey);
        if (!worker) {
            return { state: 'idle', site: siteKey };
        }
        return {
            state: worker.state,
            site: siteKey,
            headless: worker.config.headless,
            profile_dir: worker.config.userDataDir,
            target_url: worker.config.url,
        };
    }

    /**
     * Get status of all workers
     */
    getAllStatus() {
        const status = {};
        // Get status for active workers
        for (const [siteKey, worker] of this.browsers.entries()) {
            status[siteKey] = this.getState(siteKey);
        }
        return status;
    }

    /**
     * Start a browser worker for a site
     */
    async start(siteKey, config) {
        // Check if already running
        if (this.browsers.has(siteKey)) {
            const worker = this.browsers.get(siteKey);
            if (worker.state === 'running') {
                throw new Error(`Worker for ${siteKey} is already running`);
            }
        }

        try {
            // Set up profile directory
            const profileDir = config.profile_dir || path.join(this.profilesBaseDir, siteKey);
            if (!fs.existsSync(profileDir)) {
                try {
                    fs.mkdirSync(profileDir, { recursive: true });
                } catch (e) {
                    throw new Error(`Failed to create profile directory ${profileDir}: ${e.message}`);
                }
            }
            // Ensure directory is writable
            try {
                fs.accessSync(profileDir, fs.constants.W_OK);
            } catch (e) {
                throw new Error(`Profile directory ${profileDir} is not writable: ${e.message}`);
            }

            // Launch browser with persistent context
            const launchOptions = {
                headless: false,
                // headless: config.headless !== false, // Default to headless if not specified
                userDataDir: profileDir,
                args: [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-crashpad',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ],
                defaultViewport: {
                    width: config.viewport_width || 1440,
                    height: config.viewport_height || 900,
                },
            };

            // Log cache directory and verify browser exists
            const cacheDir = process.env.PUPPETEER_CACHE_DIR || '/app/.puppeteer-cache';
            console.log(`[${siteKey}] Launching browser (cache dir: ${cacheDir})`);
            
            // Try to get executable path for debugging
            try {
                const executablePath = puppeteer.executablePath();
                console.log(`[${siteKey}] Browser executable: ${executablePath}`);
                if (!fs.existsSync(executablePath)) {
                    throw new Error(`Browser executable not found at: ${executablePath}. Run: npx puppeteer browsers install chromium`);
                }
            } catch (e) {
                console.warn(`[${siteKey}] Could not verify browser executable: ${e.message}`);
            }

            const browser = await puppeteer.launch(launchOptions);

            // Create or get page
            const pages = await browser.pages();
            const page = pages.length > 0 ? pages[0] : await browser.newPage();

            // Determine URL to navigate to
            let targetUrl = config.url;
            
            // If no URL in config, try to load from worker module
            if (!targetUrl) {
                try {
                    const workerPath = path.join(__dirname, 'workers', `${siteKey}.js`);
                    if (fs.existsSync(workerPath)) {
                        const workerModule = require(workerPath);
                        if (workerModule.siteUrl) {
                            targetUrl = workerModule.siteUrl;
                            console.log(`[${siteKey}] Using URL from worker module: ${targetUrl}`);
                        }
                    }
                } catch (e) {
                    console.warn(`[${siteKey}] Could not load URL from worker module: ${e.message}`);
                }
            }

            // Navigate to site URL
            if (targetUrl) {
                console.log(`[${siteKey}] Navigating to: ${targetUrl}`);
                await page.goto(targetUrl, {
                    waitUntil: 'domcontentloaded',
                    timeout: (config.timeout_seconds || 30) * 1000,
                });
                console.log(`[${siteKey}] Navigation complete`);
            } else {
                console.warn(`[${siteKey}] No URL provided and not found in worker module. Browser opened but not navigated.`);
            }

            // Load and run site-specific worker
            const stopSignal = { isSet: false };
            let workerTask = null;
            
            try {
                const workerPath = path.join(__dirname, 'workers', `${siteKey}.js`);
                if (fs.existsSync(workerPath)) {
                    const workerModule = require(workerPath);
                    
                    // Run bootstrap if available
                    if (workerModule.bootstrap && typeof workerModule.bootstrap === 'function') {
                        console.log(`[${siteKey}] Running bootstrap...`);
                        await workerModule.bootstrap(page);
                    }
                    
                    // Start worker loop in background
                    if (workerModule.run && typeof workerModule.run === 'function') {
                        console.log(`[${siteKey}] Starting worker loop...`);
                        workerTask = workerModule.run(page, stopSignal).catch(err => {
                            console.error(`[${siteKey}] Worker error:`, err);
                        });
                    } else {
                        console.log(`[${siteKey}] No run() method found in worker module`);
                    }
                } else {
                    console.log(`[${siteKey}] No worker module found at ${workerPath}, browser will stay open`);
                }
            } catch (e) {
                console.warn(`[${siteKey}] Error loading worker module: ${e.message}`);
                // Continue anyway - browser is still running
            }

            // Store worker info
            this.browsers.set(siteKey, {
                browser,
                page,
                state: 'running',
                config: {
                    ...config,
                    url: targetUrl || config.url, // Store the actual URL used
                    userDataDir: profileDir,
                },
                startedAt: new Date(),
                stopSignal: stopSignal,
                workerTask: workerTask,
            });

            return {
                success: true,
                site: siteKey,
                state: 'running',
                message: `Worker for ${siteKey} started successfully`,
            };
        } catch (error) {
            // Clean up on error
            if (this.browsers.has(siteKey)) {
                this.browsers.delete(siteKey);
            }
            throw error;
        }
    }

    /**
     * Stop a browser worker
     */
    async stop(siteKey) {
        const worker = this.browsers.get(siteKey);
        if (!worker) {
            throw new Error(`No worker found for ${siteKey}`);
        }

        if (worker.state === 'stopped') {
            throw new Error(`Worker for ${siteKey} is already stopped`);
        }

        try {
            worker.state = 'stopping';

            // Signal worker to stop
            if (worker.stopSignal) {
                worker.stopSignal.isSet = true;
            }

            // Wait a bit for worker to finish gracefully
            if (worker.workerTask) {
                try {
                    await Promise.race([
                        worker.workerTask,
                        new Promise(resolve => setTimeout(resolve, 2000)) // Max 2s wait
                    ]);
                } catch (e) {
                    console.warn(`[${siteKey}] Error waiting for worker to stop: ${e.message}`);
                }
            }

            // Close browser
            if (worker.browser) {
                await worker.browser.close();
            }

            // Remove from map
            this.browsers.delete(siteKey);

            return {
                success: true,
                site: siteKey,
                state: 'stopped',
                message: `Worker for ${siteKey} stopped successfully`,
            };
        } catch (error) {
            // Remove even if close failed
            this.browsers.delete(siteKey);
            throw error;
        }
    }

    /**
     * Restart a browser worker
     */
    async restart(siteKey, config) {
        try {
            // Stop if running
            if (this.browsers.has(siteKey)) {
                await this.stop(siteKey);
                // Brief pause between stop and start
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            // Start again
            return await this.start(siteKey, config);
        } catch (error) {
            throw error;
        }
    }

    /**
     * Stop all workers
     */
    async stopAll() {
        const results = {};
        const siteKeys = Array.from(this.browsers.keys());

        for (const siteKey of siteKeys) {
            try {
                await this.stop(siteKey);
                results[siteKey] = { success: true };
            } catch (error) {
                results[siteKey] = { success: false, error: error.message };
            }
        }

        return results;
    }
}

module.exports = BrowserManager;
