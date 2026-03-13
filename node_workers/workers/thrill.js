/**
 * Thrill.global Puppeteer worker
 */
module.exports = {
    siteKey: 'thrill',
    siteName: 'Thrill',
    siteUrl: 'https://www.thrill.com/casino/',
    async bootstrap(page) {
        console.log('[thrill] Bootstrapping Thrill page...');
        await page.waitForTimeout(2000); // Wait for page to load
        
        // Click the Chat button before scrolling
        console.log('[thrill] Clicking Chat button...');
        try {
            // Try multiple selectors to find the chat button
            const chatButtonSelectors = [
                'button[aria-label="Chat"]',
                'button[aria-label="Chat"].focusable',
                'button.focusable[aria-label="Chat"]',
            ];
            
            let chatButtonClicked = false;
            for (const selector of chatButtonSelectors) {
                try {
                    await page.waitForSelector(selector, { timeout: 5000 });
                    await page.click(selector);
                    console.log(`[thrill] Successfully clicked Chat button using selector: ${selector}`);
                    chatButtonClicked = true;
                    await page.waitForTimeout(1000); // Wait for chat to open
                    break;
                } catch (e) {
                    console.log(`[thrill] Selector failed (${selector}): ${e.message}`);
                }
            }
            
            if (!chatButtonClicked) {
                console.warn('[thrill] Could not click the Chat button. Continuing anyway...');
            }
        } catch (error) {
            console.warn(`[thrill] Error clicking Chat button: ${error.message}. Continuing anyway...`);
        }
        
        // Find the carousel section
        console.log('[thrill] Finding carousel section...');
        const sectionBoundingBox = await page.evaluate(() => {
            // Find section containing the banners-carousel div
            const sections = document.querySelectorAll('section');
            for (const section of sections) {
                const carouselDiv = section.querySelector('div[data-testid="banners-carousel"]');
                if (carouselDiv) {
                    const rect = section.getBoundingClientRect();
                    return {
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                        found: true
                    };
                }
            }
            // Fallback: try to find the carousel div directly
            const carouselDiv = document.querySelector('div[data-testid="banners-carousel"]');
            if (carouselDiv) {
                const rect = carouselDiv.getBoundingClientRect();
                return {
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2,
                    found: true
                };
            }
            return { found: false };
        });
        
        if (sectionBoundingBox.found) {
            console.log('[thrill] Carousel section found, focusing on it...');
            // Move mouse to center of section to ensure scroll events target it
            await page.mouse.move(sectionBoundingBox.x, sectionBoundingBox.y);
            await page.waitForTimeout(500);
        } else {
            console.warn('[thrill] Carousel section not found, scrolling entire page');
        }
        
        // Scroll using mouse wheel events until reaching the end
        console.log('[thrill] Scrolling to end using mouse wheel...');
        
        let previousScrollTop = 0;
        let currentScrollTop = await page.evaluate(() => {
            // Try to find the scrollable element within the carousel section
            const sections = document.querySelectorAll('section');
            for (const section of sections) {
                const carouselDiv = section.querySelector('div[data-testid="banners-carousel"]');
                if (carouselDiv) {
                    // Check if section itself is scrollable
                    if (section.scrollHeight > section.clientHeight) {
                        return section.scrollTop;
                    }
                    // Check if carousel div is scrollable
                    if (carouselDiv.scrollHeight > carouselDiv.clientHeight) {
                        return carouselDiv.scrollTop;
                    }
                }
            }
            // Fallback to page scroll
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
            await page.waitForTimeout(300); // Wait for content to load
            
            // Check new scroll position
            currentScrollTop = await page.evaluate(() => {
                // Try to find the scrollable element within the carousel section
                const sections = document.querySelectorAll('section');
                for (const section of sections) {
                    const carouselDiv = section.querySelector('div[data-testid="banners-carousel"]');
                    if (carouselDiv) {
                        // Check if section itself is scrollable
                        if (section.scrollHeight > section.clientHeight) {
                            return section.scrollTop;
                        }
                        // Check if carousel div is scrollable
                        if (carouselDiv.scrollHeight > carouselDiv.clientHeight) {
                            return carouselDiv.scrollTop;
                        }
                    }
                }
                // Fallback to page scroll
                return window.pageYOffset || document.documentElement.scrollTop;
            });
            
            if (currentScrollTop === previousScrollTop) {
                noChangeCount++;
            } else {
                noChangeCount = 0; // Reset if scroll position changed
            }
            
            if (noChangeCount >= noChangeThreshold) {
                console.log('[thrill] Scroll position unchanged for several attempts, assuming end of scroll.');
                break;
            }
            
            scrollAttempts++;
        }
        
        // Perform a few extra scrolls to ensure we're at the very bottom
        for (let i = 0; i < 5; i++) {
            await page.mouse.wheel({ deltaY: 500 });
            await page.waitForTimeout(200);
        }
        
        // Wait a bit after scrolling down
        await page.waitForTimeout(1000);
        
        // Now scroll up to find the "Games activities" region div
        console.log('[thrill] Scrolling up to find Games activities region...');
        const gamesActivitiesDivInfo = await page.evaluate(() => {
            // Find div with role="region" and aria-label="Games activities"
            const regionDivs = document.querySelectorAll('div[role="region"]');
            
            for (const div of regionDivs) {
                const ariaLabel = div.getAttribute('aria-label');
                if (ariaLabel === 'Games activities') {
                    const rect = div.getBoundingClientRect();
                    return {
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                        scrollY: window.pageYOffset + rect.top - 100, // Position to scroll to (100px offset from top)
                        found: true
                    };
                }
            }
            
            // Fallback: try to find by classes (flex flex-col gap-20)
            const allDivs = document.querySelectorAll('div.flex.flex-col.gap-20');
            for (const div of allDivs) {
                // Verify it contains the activity feed by checking for buttons with role="row"
                const hasActivityRows = div.querySelector('button[role="row"]');
                if (hasActivityRows) {
                    const rect = div.getBoundingClientRect();
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
        
        if (gamesActivitiesDivInfo.found) {
            console.log('[thrill] Games activities region found, scrolling up to it...');
            
            // Scroll the page to bring the div into view
            await page.evaluate((scrollY) => {
                window.scrollTo({ top: scrollY, behavior: 'smooth' });
            }, gamesActivitiesDivInfo.scrollY);
            
            // Wait for scroll to complete
            await page.waitForTimeout(1000);
            
            // Move mouse to center of the div to ensure it's focused
            await page.mouse.move(gamesActivitiesDivInfo.x, gamesActivitiesDivInfo.y);
            await page.waitForTimeout(500);
            
            console.log('[thrill] Scrolled up to Games activities region');
        } else {
            console.warn('[thrill] Games activities region not found, continuing anyway');
        }
        
        // Wait a bit more after scrolling to ensure content is loaded
        await page.waitForTimeout(2000);
        console.log('[thrill] Bootstrap complete');
    },
    async run(page, stopSignal) {
        console.log('[thrill] Worker loop started - scraping usernames every 5 seconds');
        
        // Start live chat scraper in parallel (runs every 10 seconds)
        const liveChatScraperTask = module.exports.runLiveChatScraper(page, stopSignal).catch(err => {
            console.error('[thrill] Live chat scraper error:', err);
        });
        
        // Main activity feed scraper (runs every 5 seconds)
        while (!stopSignal.isSet) {
            try {
                // Wait for activity feed container to be present
                await page.waitForSelector('div.flex.flex-col-reverse button[role="row"]', { timeout: 10000 }).catch(() => {
                    console.log('[thrill] Activity feed not found, waiting...');
                });
                
                // Extract usernames from button elements
                const usernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find container with flex-col-reverse
                    const containers = document.querySelectorAll('div.flex.flex-col-reverse');
                    let targetContainer = null;
                    
                    for (const container of containers) {
                        // Check if it contains buttons with role="row"
                        const hasRowButtons = container.querySelector('button[role="row"]');
                        if (hasRowButtons) {
                            targetContainer = container;
                            break;
                        }
                    }
                    
                    if (!targetContainer) {
                        return extractedUsernames;
                    }
                    
                    // Find all buttons with role="row"
                    const rowButtons = targetContainer.querySelectorAll('button[role="row"]');
                    
                    rowButtons.forEach((rowButton, index) => {
                        // Find the username button inside this row
                        // Look for button with class containing "typ-paragraph-xsmall" and "text-foreground-text"
                        const usernameButton = rowButton.querySelector('button.typ-paragraph-xsmall.text-foreground-text');
                        
                        if (usernameButton) {
                            const username = usernameButton.textContent.trim();
                            if (username) {
                                extractedUsernames.push({
                                    index: index + 1,
                                    username: username
                                });
                            }
                        } else {
                            // Fallback: try to find any button with similar classes
                            const fallbackButton = rowButton.querySelector('button[class*="typ-paragraph"], button[class*="text-foreground-text"]');
                            if (fallbackButton) {
                                const username = fallbackButton.textContent.trim();
                                if (username) {
                                    extractedUsernames.push({
                                        index: index + 1,
                                        username: username
                                    });
                                }
                            }
                        }
                    });
                    
                    return extractedUsernames;
                });
                
                // Log usernames to console
                if (usernames.length > 0) {
                    console.log(`[thrill] Found ${usernames.length} usernames from activity feed:`);
                    usernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                } else {
                    console.log('[thrill] No usernames found in activity feed');
                }
                
                // Wait 5 seconds before next scrape
                await page.waitForTimeout(5000);
                
            } catch (error) {
                console.error(`[thrill] Error scraping usernames: ${error.message}`);
                await page.waitForTimeout(5000);
            }
        }
        
        console.log('[thrill] Worker loop stopped');
    },
    async runLiveChatScraper(page, stopSignal) {
        console.log('[thrill] Live chat scraper started - scraping usernames every 10 seconds');
        
        while (!stopSignal.isSet) {
            try {
                // Wait a bit before first scrape to ensure chat is open
                await page.waitForTimeout(2000);
                
                // Extract usernames from live chat
                // Target span elements with classes: text-foreground-light font-extrabold uppercase
                // These are inside chat message bubbles (div[data-testid="chat-message-bubble"])
                const liveChatUsernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find all chat message bubbles
                    const chatBubbles = document.querySelectorAll('div[data-testid="chat-message-bubble"]');
                    
                    chatBubbles.forEach((bubble, bubbleIndex) => {
                        // Find span elements with the specific classes: text-foreground-light font-extrabold uppercase
                        const usernameSpans = bubble.querySelectorAll('span.text-foreground-light.font-extrabold.uppercase');
                        
                        usernameSpans.forEach((span) => {
                            const username = span.textContent.trim();
                            if (username) {
                                extractedUsernames.push({
                                    index: extractedUsernames.length + 1,
                                    username: username
                                });
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
                    console.log(`[thrill] Found ${liveChatUsernames.length} usernames from live chat:`);
                    liveChatUsernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                } else {
                    console.log('[thrill] No usernames found in live chat');
                }
                
                // Wait 10 seconds before next scrape
                await page.waitForTimeout(10000);
                
            } catch (error) {
                console.error(`[thrill] Error scraping live chat usernames: ${error.message}`);
                await page.waitForTimeout(10000);
            }
        }
        
        console.log('[thrill] Live chat scraper stopped');
    },
};
