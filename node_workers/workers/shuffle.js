/**
 * Shuffle.com Puppeteer worker
 */
const { sendUsernames } = require('../usernameApiClient');

module.exports = {
    siteKey: 'shuffle',
    siteName: 'Shuffle',
    siteUrl: 'https://shuffle.com',
    async bootstrap(page) {
        console.log('[shuffle] Bootstrapping Shuffle page...');
        await page.waitForTimeout(2000); // Wait for page to load
        
        // Find and focus on the carousel section
        console.log('[shuffle] Finding carousel section...');
        const sectionBoundingBox = await page.evaluate(() => {
            // Find section with Carousel content
            const sections = document.querySelectorAll('section');
            for (const section of sections) {
                const carouselDiv = section.querySelector('div[class*="Carousel"]');
                if (carouselDiv) {
                    const rect = section.getBoundingClientRect();
                    return {
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                        found: true
                    };
                }
            }
            return { found: false };
        });
        
        if (sectionBoundingBox.found) {
            console.log('[shuffle] Carousel section found, focusing on it...');
            // Move mouse to center of section to ensure scroll events target it
            await page.mouse.move(sectionBoundingBox.x, sectionBoundingBox.y);
            await page.waitForTimeout(500);
        } else {
            console.warn('[shuffle] Carousel section not found, scrolling entire page');
        }
        
        // Scroll using mouse wheel events until reaching the end
        console.log('[shuffle] Scrolling to end using mouse wheel...');
        
        let previousScrollTop = 0;
        let currentScrollTop = await page.evaluate(() => {
            return window.pageYOffset || document.documentElement.scrollTop;
        });
        
        let scrollAttempts = 0;
        const maxScrollAttempts = 100; // Prevent infinite loop
        let noChangeCount = 0;
        
        while (scrollAttempts < maxScrollAttempts) {
            previousScrollTop = currentScrollTop;
            
            // Simulate mouse wheel scroll down
            await page.mouse.wheel({ deltaY: 1000 });
            await page.waitForTimeout(300); // Wait for content to load
            
            // Check new scroll position
            currentScrollTop = await page.evaluate(() => {
                return window.pageYOffset || document.documentElement.scrollTop;
            });
            
            // If scroll position hasn't changed, increment no-change counter
            if (currentScrollTop === previousScrollTop) {
                noChangeCount++;
                
                // If no change for 5 consecutive attempts, we've reached the end
                if (noChangeCount >= 5) {
                    console.log('[shuffle] Reached end of scrollable content');
                    break;
                }
            } else {
                // Reset counter if scroll position changed
                noChangeCount = 0;
            }
            
            scrollAttempts++;
        }
        
        // Do a few more scrolls to ensure we're at the very bottom
        for (let i = 0; i < 3; i++) {
            await page.mouse.wheel({ deltaY: 500 });
            await page.waitForTimeout(200);
        }
        
        // Wait a bit more after scrolling to ensure content is loaded
        await page.waitForTimeout(2000);
        console.log('[shuffle] Bootstrap complete');
    },
    async run(page, stopSignal) {
        console.log('[shuffle] Worker loop started - scraping usernames every 5 seconds');
        
        while (!stopSignal.isSet) {
            try {
                // Wait for table to be present
                // Use stable selector: tbody with data-testid or just tbody
                await page.waitForSelector('tbody[data-testid="table-body"], table tbody', { timeout: 10000 }).catch(() => {
                    console.log('[shuffle] Table not found, waiting...');
                });
                
                // Extract usernames from table rows
                const usernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find table body - use data-testid or just find any tbody in a table
                    let tbody = document.querySelector('tbody[data-testid="table-body"]');
                    if (!tbody) {
                        // Fallback: find first tbody in a table
                        const table = document.querySelector('table');
                        if (table) {
                            tbody = table.querySelector('tbody');
                        }
                    }
                    
                    if (!tbody) {
                        return extractedUsernames;
                    }
                    
                    // Find all rows in the tbody
                    const rows = tbody.querySelectorAll('tr');
                    
                    rows.forEach((row, index) => {
                        // Find button in the row (usually in first td)
                        const button = row.querySelector('button');
                        if (button) {
                            // Find span with VipBadge or VipIcon (or any span in button)
                            const span = button.querySelector('span');
                            
                            if (span) {
                                // Get all text nodes in the button
                                // The username is the text that's not inside the span
                                const buttonText = button.textContent.trim();
                                
                                // Get text content of the span
                                const spanText = span.textContent.trim();
                                
                                // Remove span text from button text to get username
                                // The username comes after the span in the button
                                let username = buttonText.replace(spanText, '').trim();
                                
                                // Clean up any extra whitespace
                                username = username.replace(/\s+/g, ' ').trim();
                                
                                if (username) {
                                    extractedUsernames.push({
                                        index: index + 1,
                                        username: username
                                    });
                                }
                            } else {
                                // Fallback: if no span found, get all button text
                                // and remove text from any child elements
                                const buttonText = button.textContent.trim();
                                const childElements = button.querySelectorAll('*');
                                let childText = '';
                                childElements.forEach(child => {
                                    childText += child.textContent.trim();
                                });
                                
                                const username = buttonText.replace(childText, '').trim();
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
                    console.log(`[shuffle] Found ${usernames.length} usernames:`);
                    usernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                    
                    // Send usernames to API
                    const apiResult = await sendUsernames('shuffle', usernames);
                    if (apiResult.success) {
                        console.log(`[shuffle] Sent ${apiResult.added} usernames to API (${apiResult.skipped} skipped)`);
                    }
                } else {
                    console.log('[shuffle] No usernames found');
                }
                
                // Wait 5 seconds before next scrape
                await page.waitForTimeout(5000);
                
            } catch (error) {
                console.error(`[shuffle] Error scraping usernames: ${error.message}`);
                await page.waitForTimeout(5000);
            }
        }
        
        console.log('[shuffle] Worker loop stopped');
    },
};
