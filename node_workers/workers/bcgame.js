// const { sleep } = require('../utils');

/**
 * BC.Game Puppeteer worker
 */
module.exports = {
    siteKey: 'bcgame',
    siteName: 'BC.Game',
    siteUrl: 'https://bc.game',
    async bootstrap(page) {
        console.log('[bcgame] Bootstrapping BC.Game page...');
        // await sleep(2000);
        await page.waitForTimeout(2000);

        // Click the live chat button: button containing div.color_icon_img.chat (same pattern as roobet)
        console.log('[bcgame] Looking for live chat button...');
        const maxRetries = 10;
        const retryDelay = 2000;
        let chatButtonClicked = false;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const clicked = await page.evaluate(() => {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        const chatIcon = btn.querySelector('div.color_icon_img.chat');
                        if (chatIcon) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                });

                if (clicked) {
                    console.log(`[bcgame] Clicked live chat button (attempt ${attempt})`);
                    chatButtonClicked = true;
                    // await sleep(1500);
                    await page.waitForTimeout(1500);
                    break;
                }

                if (attempt < maxRetries) {
                    console.log(`[bcgame] Live chat button not found, retrying in ${retryDelay / 1000}s... (${attempt}/${maxRetries})`);
                    // await sleep(retryDelay);
                    await page.waitForTimeout(retryDelay);
                }
            } catch (error) {
                console.log(`[bcgame] Error during chat button search (attempt ${attempt}): ${error.message}`);
                if (attempt < maxRetries) await page.waitForTimeout(retryDelay);
            }
        }

        if (!chatButtonClicked) {
            console.warn(`[bcgame] Could not find or click the live chat button after ${maxRetries} attempts. Continuing anyway...`);
        }
        
        // First scroll to the end of the page, wait 5 seconds, then scroll back up to "All Bingo Games" section
        console.log('[bcgame] Scrolling to end of page first...');
        try {
            // Scroll down to the end using mouse wheel events
            let previousScrollTop = 0;
            let currentScrollTop = await page.evaluate(() => {
                return window.pageYOffset || document.documentElement.scrollTop;
            });
            
            let scrollAttempts = 0;
            const maxScrollAttempts = 100; // Prevent infinite loop
            let noChangeCount = 0;
            const noChangeThreshold = 5; // How many times scroll position can remain unchanged before stopping
            
            while (scrollAttempts < maxScrollAttempts) {
                previousScrollTop = currentScrollTop;
                
                // Simulate mouse wheel scroll down
                await page.mouse.wheel({ deltaY: 1000 });
                // await sleep(300); // Wait for content to load
                await page.waitForTimeout(300);
                
                // Check new scroll position
                currentScrollTop = await page.evaluate(() => {
                    return window.pageYOffset || document.documentElement.scrollTop;
                });
                
                if (currentScrollTop === previousScrollTop) {
                    noChangeCount++;
                } else {
                    noChangeCount = 0; // Reset if scroll position changed
                }
                
                if (noChangeCount >= noChangeThreshold) {
                    console.log('[bcgame] Reached end of page');
                    break;
                }
                
                scrollAttempts++;
            }
            
            // Perform a few extra scrolls to ensure we're at the very bottom
            for (let i = 0; i < 5; i++) {
                await page.mouse.wheel({ deltaY: 500 });
                // await sleep(200);
                await page.waitForTimeout(200);
            }
            
            // Wait 5 seconds after scrolling to end
            console.log('[bcgame] Waiting 5 seconds after reaching end of page...');
            // await sleep(5000);
            await page.waitForTimeout(5000);
            
            // Now scroll back up to "All Bingo Games" section
            console.log('[bcgame] Scrolling back up to "All Bingo Games" section...');
            
            // Find the target div element that contains h2 with "All Bingo Games"
            const targetElementInfo = await page.evaluate(() => {
                // Find div with classes: mt-2 flex items-center sm:mt-6 h-8
                // This div contains the h2 with "All Bingo Games"
                const divs = document.querySelectorAll('div.mt-2.flex.items-center, div[class*="mt-2"][class*="flex"][class*="items-center"]');
                
                for (const div of divs) {
                    // Check if this div contains an h2 with text "All Bingo Games"
                    const h2 = div.querySelector('h2.flex.items-center.text-base.font-extrabold.text-primary, h2[class*="text-base"][class*="font-extrabold"][class*="text-primary"]');
                    if (h2) {
                        const text = h2.textContent.trim();
                        // Check if text is "All Bingo Games"
                        if (text === 'All Bingo Games' || text.includes('All Bingo Games')) {
                            const rect = div.getBoundingClientRect();
                            return {
                                x: rect.x + rect.width / 2,
                                y: rect.y + rect.height / 2,
                                scrollY: window.pageYOffset + rect.top - 100, // Position to scroll to (100px offset from top)
                                found: true
                            };
                        }
                    }
                }
                
                // Fallback: try to find h2 directly if div not found
                const h2Elements = document.querySelectorAll('h2.flex.items-center.text-base.font-extrabold.text-primary, h2[class*="text-base"][class*="font-extrabold"][class*="text-primary"]');
                for (const h2 of h2Elements) {
                    const text = h2.textContent.trim();
                    if (text === 'All Bingo Games' || text.includes('All Bingo Games')) {
                        const rect = h2.getBoundingClientRect();
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            scrollY: window.pageYOffset + rect.top - 100,
                            found: true
                        };
                    }
                }
                
                return { found: false };
            });
            
            if (targetElementInfo.found) {
                console.log('[bcgame] Found "All Bingo Games" section, scrolling up to it...');
                
                // Scroll the page to bring the element into view
                await page.evaluate((scrollY) => {
                    window.scrollTo({ top: scrollY, behavior: 'smooth' });
                }, targetElementInfo.scrollY);
                
                // Wait for scroll to complete
                // await sleep(1000);
                await page.waitForTimeout(1000);
                
                // Move mouse to center of the div and use mouse wheel for fine adjustment
                await page.mouse.move(targetElementInfo.x, targetElementInfo.y);
                // await sleep(500);
                await page.waitForTimeout(500);
                
                console.log('[bcgame] Scrolled up to "All Bingo Games" section');
            } else {
                console.warn('[bcgame] "All Bingo Games" section not found after scrolling');
            }
        } catch (error) {
            console.warn(`[bcgame] Error scrolling: ${error.message}. Continuing anyway...`);
        }
        
        // Wait a bit after scrolling
        // await sleep(1000);
        await page.waitForTimeout(1000);
        
        console.log('[bcgame] Bootstrap complete');
    },
    async run(page, stopSignal) {
        console.log('[bcgame] Worker loop started');

        // Start activity feed scraper (runs every 5 seconds)
        const activityFeedScraperTask = (async () => {
            while (!stopSignal.isSet) {
                try {
                    // Wait for activity feed table to be present
                    await page.waitForSelector('tbody', { timeout: 10000 }).catch(() => {
                        console.log('[bcgame] Activity feed table not found, waiting...');
                    });
                    
                    // Extract usernames from activity feed
                    const usernames = await page.evaluate(() => {
                        const extractedUsernames = [];
                        
                        // Find the table body
                        const tbody = document.querySelector('tbody');
                        if (!tbody) {
                            return extractedUsernames;
                        }
                        
                        // Find all links with href starting with "/user/profile/"
                        const usernameLinks = tbody.querySelectorAll('a[href^="/user/profile/"]');
                        
                        usernameLinks.forEach((link, index) => {
                            // Check if link has the expected classes
                            const hasExpectedClasses = link.classList.contains('hover:underline') || 
                                                      link.classList.contains('inactive') ||
                                                      link.getAttribute('class')?.includes('hover:underline');
                            
                            if (hasExpectedClasses || link.href.includes('/user/profile/')) {
                                const username = link.textContent.trim();
                                if (username) {
                                    extractedUsernames.push({
                                        index: index + 1,
                                        username: username
                                    });
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
                        console.log(`[bcgame] Found ${usernames.length} usernames from activity feed:`);
                        usernames.forEach(item => {
                            console.log(`  [${item.index}] ${item.username}`);
                        });
                    } else {
                        console.log('[bcgame] No usernames found in activity feed');
                    }
                    
                    // Wait 5 seconds before next scrape
                    // await sleep(5000);
                    await page.waitForTimeout(5000);
                    
                } catch (error) {
                    console.error(`[bcgame] Error scraping activity feed usernames: ${error.message}`);
                    // await sleep(5000);
                    await page.waitForTimeout(5000);
                }
            }
            console.log('[bcgame] Activity feed scraper stopped');
        })();

        // Start live chat scraper in parallel (runs every 10 seconds)
        const liveChatScraperTask = module.exports.runLiveChatScraper(page, stopSignal).catch(err => {
            console.error('[bcgame] Live chat scraper error:', err);
        });

        await Promise.all([activityFeedScraperTask, liveChatScraperTask]);
        console.log('[bcgame] Worker loop stopped');
    },
    async runLiveChatScraper(page, stopSignal) {
        console.log('[bcgame] Live chat scraper started - scraping usernames every 10 seconds');

        while (!stopSignal.isSet) {
            try {
                // Wait a bit before first scrape to ensure chat is open
                // await sleep(2000);
                await page.waitForTimeout(2000);

                const liveChatUsernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find the scroll container (chat container)
                    const scrollContainer = document.querySelector('div.scroll-container');
                    if (!scrollContainer) {
                        return extractedUsernames;
                    }
                    
                    // Find all message boxes (divs with id starting with "box-")
                    const messageBoxes = scrollContainer.querySelectorAll('div[id^="box-"]');
                    
                    messageBoxes.forEach((box) => {
                        // Find the link with href starting with "/user/profile/"
                        const usernameLink = box.querySelector('a[href^="/user/profile/"]');
                        if (usernameLink) {
                            // Find the span with the username classes
                            const usernameSpan = usernameLink.querySelector('span.max-52.overflow-hidden.text-ellipsis.whitespace-nowrap.text-secondary.font-semibold');
                            
                            if (usernameSpan) {
                                const username = usernameSpan.textContent.trim();
                                if (username) {
                                    extractedUsernames.push({
                                        username: username
                                    });
                                }
                            } else {
                                // Fallback: try to find any span inside the link
                                const fallbackSpan = usernameLink.querySelector('span');
                                if (fallbackSpan) {
                                    const username = fallbackSpan.textContent.trim();
                                    if (username) {
                                        extractedUsernames.push({
                                            username: username
                                        });
                                    }
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

                // Log live chat usernames to console
                if (liveChatUsernames.length > 0) {
                    console.log(`[bcgame] Found ${liveChatUsernames.length} usernames from live chat:`);
                    liveChatUsernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                } else {
                    console.log('[bcgame] No usernames found in live chat');
                }

                // Wait 10 seconds before next scrape
                // await sleep(10000);
                await page.waitForTimeout(10000);

            } catch (error) {
                console.error(`[bcgame] Error scraping live chat usernames: ${error.message}`);
                // await sleep(10000);
                await page.waitForTimeout(10000);
            }
        }
        console.log('[bcgame] Live chat scraper stopped');
    },
};
