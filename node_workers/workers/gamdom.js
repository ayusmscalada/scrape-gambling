/**
 * Gamdom.com Puppeteer worker
 */
module.exports = {
    siteKey: 'gamdom',
    siteName: 'Gamdom',
    siteUrl: 'https://gamdom.com',
    async bootstrap(page) {
        console.log('[gamdom] Bootstrapping Gamdom page...');
        await page.waitForTimeout(2000); // Wait for page to load
        
        // Click the live chat button
        // Retry up to 10 times every 2 seconds if not clicked
        console.log('[gamdom] Looking for live chat button...');
        const maxRetries = 10;
        const retryDelay = 2000; // 2 seconds
        let chatButtonClicked = false;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                // Try multiple selectors to find the chat button
                const chatButtonSelectors = [
                    'button[data-testid="iconChatButton"]', // Most specific
                    'button i.icon-Chat', // Parent of icon with class
                    'button.MuiIconButton-root i.icon-Chat', // More specific
                    'button.MuiButtonBase-root.MuiIconButton-root i.icon-Chat', // Even more specific
                    'button[type="button"] i.icon-Chat', // Type + icon
                    'button i[class*="icon-Chat"]', // Icon with class containing icon-Chat
                ];
                
                for (const selector of chatButtonSelectors) {
                    try {
                        // Try to find the button by the icon first (most reliable)
                        if (selector.includes('i.icon-Chat') || selector.includes('i[class*="icon-Chat"]')) {
                            // Find the icon, then get its parent button
                            const icon = await page.$(selector);
                            if (icon) {
                                const button = await page.evaluateHandle((iconEl) => {
                                    return iconEl.closest('button');
                                }, icon);
                                
                                if (button && button.asElement()) {
                                    await button.asElement().click();
                                    console.log(`[gamdom] Successfully clicked live chat button (attempt ${attempt}) using icon selector: ${selector}`);
                                    chatButtonClicked = true;
                                    await page.waitForTimeout(1500); // Wait for chat panel to open
                                    break;
                                }
                            }
                        } else {
                            // Direct button selector
                            const button = await page.$(selector);
                            if (button) {
                                // Verify it has the chat icon
                                const hasChatIcon = await page.evaluate((btn) => {
                                    const icon = btn.querySelector('i.icon-Chat, i[class*="icon-Chat"]');
                                    return icon !== null;
                                }, button);
                                
                                if (hasChatIcon) {
                                    await button.click();
                                    console.log(`[gamdom] Successfully clicked live chat button (attempt ${attempt}) using selector: ${selector}`);
                                    chatButtonClicked = true;
                                    await page.waitForTimeout(1500); // Wait for chat panel to open
                                    break;
                                }
                            }
                        }
                    } catch (e) {
                        // Continue to next selector
                        continue;
                    }
                }
                
                if (chatButtonClicked) {
                    break; // Successfully clicked, exit retry loop
                }
                
                // If not found, wait before retrying
                if (attempt < maxRetries) {
                    console.log(`[gamdom] Live chat button not found, retrying in ${retryDelay/1000} seconds... (attempt ${attempt}/${maxRetries})`);
                    await page.waitForTimeout(retryDelay);
                }
                
            } catch (error) {
                console.log(`[gamdom] Error during chat button search (attempt ${attempt}): ${error.message}`);
                if (attempt < maxRetries) {
                    await page.waitForTimeout(retryDelay);
                }
            }
        }
        
        if (!chatButtonClicked) {
            console.warn(`[gamdom] Could not find or click the live chat button after ${maxRetries} attempts. Continuing anyway...`);
        }
        
        // Scroll down to the activity feed area before scraping
        console.log('[gamdom] Scrolling to activity feed area...');
        try {
            // Find the div with class pattern "sc-izgFkT" (activity feed container)
            const activityFeedFound = await page.evaluate(() => {
                // Look for div with class starting with "sc-izgFkT"
                const divs = document.querySelectorAll('div');
                for (const div of divs) {
                    const classList = Array.from(div.classList);
                    if (classList.some(cls => cls.startsWith('sc-izgFkT'))) {
                        // Check if it contains MuiTabs or activity feed structure
                        const hasTabs = div.querySelector('.MuiTabs-root, .MuiBox-root');
                        if (hasTabs) {
                            div.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            return true;
                        }
                    }
                }
                return false;
            });
            
            if (activityFeedFound) {
                console.log('[gamdom] Scrolled to activity feed area');
                await page.waitForTimeout(1000); // Wait for scroll to complete
            } else {
                console.log('[gamdom] Activity feed area not found, scrolling page down');
                // Fallback: scroll page down
                await page.evaluate(() => {
                    window.scrollTo({ top: document.body.scrollHeight / 2, behavior: 'smooth' });
                });
                await page.waitForTimeout(1000);
            }
        } catch (error) {
            console.log(`[gamdom] Error scrolling to activity feed: ${error.message}`);
        }
        
        console.log('[gamdom] Bootstrap complete');
    },
    async run(page, stopSignal) {
        console.log('[gamdom] Worker loop started - scraping usernames from activity feed every 5 seconds');
        
        while (!stopSignal.isSet) {
            try {
                // Wait for activity feed table to be present
                await page.waitForSelector('tbody.MuiTableBody-root, tbody', { timeout: 10000 }).catch(() => {
                    console.log('[gamdom] Activity feed table not found, waiting...');
                });
                
                // Extract usernames from activity feed
                const usernames = await page.evaluate(() => {
                    const usernames = [];
                    // Find all table rows in the activity feed
                    const rows = document.querySelectorAll('tbody.MuiTableBody-root tr, tbody tr');
                    
                    rows.forEach((row) => {
                        // Get the 2nd td (index 1)
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            const secondCell = cells[1];
                            // Find the username span with class pattern "sc-*" (random class names)
                            // Look for span elements with classes starting with "sc-"
                            const spans = secondCell.querySelectorAll('span');
                            for (const span of spans) {
                                const classList = span.classList;
                                // Check if any class starts with "sc-"
                                const hasScClass = Array.from(classList).some(cls => cls.startsWith('sc-'));
                                if (hasScClass) {
                                    const username = span.textContent.trim();
                                    // Filter out invalid usernames like "Hidden user"
                                    if (username && username.toLowerCase() !== 'hidden user') {
                                        usernames.push(username);
                                        break; // Found username in this cell, move to next row
                                    }
                                }
                            }
                        }
                    });
                    
                    return usernames;
                });
                
                if (usernames.length > 0) {
                    console.log(`[gamdom] Found ${usernames.length} usernames from activity feed:`, usernames);
                } else {
                    console.log('[gamdom] No usernames found in activity feed');
                }
                
            } catch (error) {
                console.error('[gamdom] Error scraping activity feed:', error.message);
            }
            
            // Wait 5 seconds before next scrape
            await page.waitForTimeout(5000);
        }
    },
};
