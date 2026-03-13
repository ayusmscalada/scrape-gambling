/**
 * Winna.com Puppeteer worker
 */
module.exports = {
    siteKey: 'winna',
    siteName: 'Winna',
    siteUrl: 'https://winna.com',
    async bootstrap(page) {
        console.log('[winna] Bootstrapping Winna page...');
        await page.waitForTimeout(2000); // Wait for page to load
        console.log('[winna] Bootstrap complete');
    },
    async run(page, stopSignal) {
        console.log('[winna] Worker loop started - scraping usernames every 10 seconds');
        
        while (!stopSignal.isSet) {
            try {
                // ===== PART 1: Scrape usernames from table =====
                // Wait for table to be present
                await page.waitForSelector('tbody.text-13', { timeout: 10000 }).catch(() => {
                    console.log('[winna] Table not found, waiting...');
                });
                
                // Extract usernames from table rows
                const tableUsernames = await page.evaluate(() => {
                    const rows = document.querySelectorAll('tbody.text-13 tr');
                    const extractedUsernames = [];
                    
                    rows.forEach((row, index) => {
                        // Get first td in the row
                        const firstTd = row.querySelector('td:first-child');
                        if (firstTd) {
                            // Find the username span - try multiple selectors
                            // The span has classes: cursor-pointer transition-colors hover:text-accent-blue truncate
                            let usernameSpan = firstTd.querySelector('span.cursor-pointer.transition-colors.truncate');
                            
                            // If not found, try finding by text content (not "Hidden")
                            if (!usernameSpan) {
                                const allSpans = firstTd.querySelectorAll('span');
                                for (const span of allSpans) {
                                    const text = span.textContent.trim();
                                    if (text && text !== 'Hidden' && span.classList.contains('cursor-pointer')) {
                                        usernameSpan = span;
                                        break;
                                    }
                                }
                            }
                            
                            if (usernameSpan) {
                                const username = usernameSpan.textContent.trim();
                                if (username && username !== 'Hidden') {
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
                
                // Log usernames from table to console
                if (tableUsernames.length > 0) {
                    console.log(`[winna] Found ${tableUsernames.length} usernames from table:`);
                    tableUsernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                } else {
                    console.log('[winna] No usernames found in table');
                }
                
                // ===== PART 2: Scrape usernames from div structure =====
                // Wait for the container div to be present
                await page.waitForSelector('div.flex.w-full.flex-col-reverse', { timeout: 10000 }).catch(() => {
                    console.log('[winna] Container div not found, waiting...');
                });
                
                // Extract usernames from the div structure
                const divUsernames = await page.evaluate(() => {
                    const extractedUsernames = [];
                    
                    // Find the container div with class "flex w-full flex-col-reverse gap-1 overflow-y-scroll overscroll-contain"
                    const container = document.querySelector('div.flex.w-full.flex-col-reverse.gap-1.overflow-y-scroll');
                    if (!container) {
                        return extractedUsernames;
                    }
                    
                    // Find all divs with class "group relative flex flex-col gap-2 rounded-lg px-2 py-2 pb-[10px] duration-300 bg-body-level-3"
                    const groupDivs = container.querySelectorAll('div.group.relative.flex.flex-col.gap-2.rounded-lg');
                    
                    groupDivs.forEach((groupDiv, index) => {
                        // Find the username span inside this group div
                        // The span has classes: hover:text-accent-blue cursor-pointer transition-colors
                        const usernameSpan = groupDiv.querySelector('span.hover\\:text-accent-blue.cursor-pointer.transition-colors');
                        
                        if (usernameSpan) {
                            const username = usernameSpan.textContent.trim();
                            if (username) {
                                extractedUsernames.push({
                                    index: index + 1,
                                    username: username
                                });
                            }
                        }
                    });
                    
                    return extractedUsernames;
                });
                
                // Log usernames from divs to console
                if (divUsernames.length > 0) {
                    console.log(`[winna] Found ${divUsernames.length} usernames from divs:`);
                    divUsernames.forEach(item => {
                        console.log(`  [${item.index}] ${item.username}`);
                    });
                } else {
                    console.log('[winna] No usernames found in divs');
                }
                
                // Wait 10 seconds before next scrape
                await page.waitForTimeout(10000);
                
            } catch (error) {
                console.error(`[winna] Error scraping usernames: ${error.message}`);
                await page.waitForTimeout(10000);
            }
        }
        
        console.log('[winna] Worker loop stopped');
    },
};
