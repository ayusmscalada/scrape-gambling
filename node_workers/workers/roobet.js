const { sleep } = require('../utils');

/**
 * Roobet.com Puppeteer worker
 */
const { sendUsernames } = require('../usernameApiClient');

module.exports = {
    siteKey: 'roobet',
    siteName: 'Roobet',
    siteUrl: 'https://roobet.com',
    async bootstrap(page) {
        console.log('[roobet] Bootstrapping Roobet page...');
        await sleep(2000);

        // Click the live chat button: MuiIconButton with aria-haspopup + data-border-outline and chat SVG (path d contains M7.29412 / 8.18823)
        console.log('[roobet] Looking for live chat button...');
        const maxRetries = 10;
        const retryDelay = 2000;
        let chatButtonClicked = false;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const clicked = await page.evaluate(() => {
                    const buttons = document.querySelectorAll('button[aria-haspopup="true"][data-border-outline="true"]');
                    for (const btn of buttons) {
                        const svg = btn.querySelector('svg');
                        if (!svg) continue;
                        const path = svg.querySelector('path');
                        if (!path) continue;
                        const d = path.getAttribute('d') || '';
                        // Chat bubble icon from Roobet: path contains this signature
                        if (d.includes('M7.29412') && d.includes('8.18823')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                });

                if (clicked) {
                    console.log(`[roobet] Clicked live chat button (attempt ${attempt})`);
                    chatButtonClicked = true;
                    await sleep(1500);
                    break;
                }

                if (attempt < maxRetries) {
                    console.log(`[roobet] Live chat button not found, retrying in ${retryDelay / 1000}s... (${attempt}/${maxRetries})`);
                    await sleep(retryDelay);
                }
            } catch (error) {
                console.log(`[roobet] Error during chat button search (attempt ${attempt}): ${error.message}`);
                if (attempt < maxRetries) await sleep(retryDelay);
            }
        }

        if (!chatButtonClicked) {
            console.warn(`[roobet] Could not find or click the live chat button after ${maxRetries} attempts. Continuing anyway...`);
        }

        console.log('[roobet] Bootstrap complete');
    },
    async run(page, stopSignal) {
        console.log('[roobet] Worker loop started - scraping usernames every 5 seconds');
        
        // Start live chat scraper in parallel (runs every 10 seconds)
        const liveChatScraperTask = module.exports.runLiveChatScraper(page, stopSignal).catch(err => {
            console.error('[roobet] Live chat scraper error:', err);
        });
        
        // Main activity feed scraper (runs every 5 seconds)
        while (!stopSignal.isSet) {
            try {
                // Wait for activity feed table to be present
                await page.waitForSelector('tbody.MuiTableBody-root, tbody', { timeout: 10000 }).catch(() => {
                    console.log('[roobet] Activity feed table not found, waiting...');
                });
                
                // Extract usernames from activity feed
                const usernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find the table body
                    const tbody = document.querySelector('tbody.MuiTableBody-root') || document.querySelector('tbody');
                    if (!tbody) {
                        return extractedUsernames;
                    }
                    
                    // Find all links with MuiLink-root class that contain username spans
                    const links = tbody.querySelectorAll('a.MuiLink-root');
                    
                    links.forEach((link, index) => {
                        // Find span with data-mention="false" inside the link
                        const usernameSpan = link.querySelector('span[data-mention="false"]');
                        
                        if (usernameSpan) {
                            const username = usernameSpan.textContent.trim();
                            if (username) {
                                extractedUsernames.push({
                                    index: index + 1,
                                    username: username
                                });
                            }
                        } else {
                            // Fallback: try to extract from href attribute
                            // href format: /?modal=profile&user=Jonni48
                            const href = link.getAttribute('href');
                            if (href && href.includes('user=')) {
                                const match = href.match(/user=([^&]+)/);
                                if (match && match[1]) {
                                    extractedUsernames.push({
                                        index: index + 1,
                                        username: match[1]
                                    });
                                }
                            }
                        }
                    });
                    
                    // Remove duplicates
                    const uniqueUsernames = [];
                    const seen = new Set();
                    extractedUsernames.forEach(item => {
                        if (!seen.has(item.username)) {
                            seen.add(item.username);
                            uniqueUsernames.push(item);
                        }
                    });
                    
                    return uniqueUsernames.map((item, idx) => ({ index: idx + 1, username: item.username }));
                });
                
                // Log usernames to console
                if (usernames.length > 0) {
                    console.log(`[roobet] Found ${usernames.length} usernames from activity feed:`);
                    usernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                    
                    // Send usernames to API
                    const apiResult = await sendUsernames('roobet', usernames);
                    if (apiResult.success) {
                        console.log(`[roobet] Sent ${apiResult.added} usernames to API (${apiResult.skipped} skipped)`);
                    }
                } else {
                    console.log('[roobet] No usernames found in activity feed');
                }
                
                // Wait 5 seconds before next scrape
                await sleep(5000);
                
            } catch (error) {
                console.error(`[roobet] Error scraping usernames: ${error.message}`);
                await sleep(5000);
            }
        }
        
        console.log('[roobet] Worker loop stopped');
    },
    async runLiveChatScraper(page, stopSignal) {
        console.log('[roobet] Live chat scraper started - scraping usernames every 10 seconds');
        
        while (!stopSignal.isSet) {
            try {
                // Wait a bit before first scrape to ensure chat is open
                await sleep(2000);
                
                // Extract usernames from live chat messages
                const liveChatUsernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find all chat message containers (div.css-12b57lc)
                    const chatMessages = document.querySelectorAll('div.css-12b57lc');
                    
                    chatMessages.forEach((messageContainer) => {
                        // Find links with class css-aih8kn (chat username links)
                        const usernameLinks = messageContainer.querySelectorAll('a.MuiLink-root.css-aih8kn');
                        
                        usernameLinks.forEach((link) => {
                            // Find span with data-mention="false" inside the link
                            const usernameSpan = link.querySelector('span[data-mention="false"]');
                            
                            if (usernameSpan) {
                                // Extract username (remove trailing colon if present)
                                let username = usernameSpan.textContent.trim();
                                // Remove trailing colon
                                if (username.endsWith(':')) {
                                    username = username.slice(0, -1).trim();
                                }
                                
                                if (username) {
                                    extractedUsernames.push({
                                        username: username
                                    });
                                }
                            } else {
                                // Fallback: try to extract from href attribute
                                // href format: /?modal=profile&user=xSoda212x
                                const href = link.getAttribute('href');
                                if (href && href.includes('user=')) {
                                    const match = href.match(/user=([^&]+)/);
                                    if (match && match[1]) {
                                        extractedUsernames.push({
                                            username: match[1]
                                        });
                                    }
                                }
                            }
                        });
                    });
                    
                    // Remove duplicates
                    const uniqueUsernames = [];
                    const seen = new Set();
                    extractedUsernames.forEach(item => {
                        if (!seen.has(item.username)) {
                            seen.add(item.username);
                            uniqueUsernames.push(item);
                        }
                    });
                    
                    return uniqueUsernames.map((item, idx) => ({ index: idx + 1, username: item.username }));
                });
                
                // Log live chat usernames to console
                if (liveChatUsernames.length > 0) {
                    console.log(`[roobet] Found ${liveChatUsernames.length} usernames from live chat:`);
                    liveChatUsernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                    
                    // Send usernames to API
                    const apiResult = await sendUsernames('roobet', liveChatUsernames);
                    if (apiResult.success) {
                        console.log(`[roobet] Sent ${apiResult.added} live chat usernames to API (${apiResult.skipped} skipped)`);
                    }
                } else {
                    console.log('[roobet] No usernames found in live chat');
                }
                
                // Wait 10 seconds before next scrape
                await sleep(10000);
                
            } catch (error) {
                console.error(`[roobet] Error scraping live chat usernames: ${error.message}`);
                await sleep(10000);
            }
        }
        
        console.log('[roobet] Live chat scraper stopped');
    },
};
