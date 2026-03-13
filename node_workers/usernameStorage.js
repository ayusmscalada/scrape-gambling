/**
 * Username storage and CSV export module
 * Stores scraped usernames with platform information and exports to CSV
 */

const fs = require('fs');
const path = require('path');

class UsernameStorage {
    constructor() {
        this.usernames = []; // Array of {username, platform, timestamp}
        this.csvFilePath = path.join(__dirname, '..', 'scraped_usernames.csv');
        this.autoSaveInterval = null;
        this.autoSaveIntervalMs = 30000; // Auto-save every 30 seconds
        
        // Initialize CSV file with headers if it doesn't exist
        this.initializeCSV();
        
        // Start auto-save interval
        this.startAutoSave();
    }

    /**
     * Initialize CSV file with headers
     */
    initializeCSV() {
        try {
            // Check if file exists
            if (!fs.existsSync(this.csvFilePath)) {
                // Create directory if it doesn't exist
                const dir = path.dirname(this.csvFilePath);
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                
                // Write CSV headers
                const headers = 'timestamp,username,platform\n';
                fs.writeFileSync(this.csvFilePath, headers, 'utf8');
                console.log(`[UsernameStorage] Initialized CSV file: ${this.csvFilePath}`);
            }
        } catch (error) {
            console.error(`[UsernameStorage] Error initializing CSV: ${error.message}`);
        }
    }

    /**
     * Add a username entry
     * @param {string} username - The username
     * @param {string} platform - The platform name (e.g., 'stake', 'roobet', 'bcgame')
     */
    addUsername(username, platform) {
        if (!username || !platform) {
            console.warn(`[UsernameStorage] Invalid entry: username=${username}, platform=${platform}`);
            return false;
        }

        const entry = {
            username: username.trim(),
            platform: platform.trim().toLowerCase(),
            timestamp: new Date().toISOString()
        };

        // Check for duplicates (same username + platform within last 5 minutes)
        const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
        const isDuplicate = this.usernames.some(item => 
            item.username === entry.username && 
            item.platform === entry.platform &&
            item.timestamp > fiveMinutesAgo
        );

        if (!isDuplicate) {
            this.usernames.push(entry);
            console.log(`[UsernameStorage] Added: ${entry.username} (${entry.platform})`);
            return true;
        } else {
            console.log(`[UsernameStorage] Skipped duplicate: ${entry.username} (${entry.platform})`);
            return false;
        }
    }

    /**
     * Add multiple usernames
     * @param {Array} entries - Array of {username, platform} objects
     */
    addUsernames(entries) {
        if (!Array.isArray(entries)) {
            console.warn(`[UsernameStorage] Invalid entries: expected array, got ${typeof entries}`);
            return { added: 0, skipped: 0 };
        }

        let added = 0;
        let skipped = 0;

        entries.forEach(entry => {
            if (this.addUsername(entry.username, entry.platform)) {
                added++;
            } else {
                skipped++;
            }
        });

        return { added, skipped };
    }

    /**
     * Get all stored usernames
     * @param {Object} options - Filter options
     * @param {string} options.platform - Filter by platform
     * @param {number} options.limit - Limit number of results
     */
    getUsernames(options = {}) {
        let results = [...this.usernames];

        // Filter by platform if specified
        if (options.platform) {
            results = results.filter(item => 
                item.platform.toLowerCase() === options.platform.toLowerCase()
            );
        }

        // Sort by timestamp (newest first)
        results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        // Limit results if specified
        if (options.limit && options.limit > 0) {
            results = results.slice(0, options.limit);
        }

        return results;
    }

    /**
     * Get statistics
     */
    getStats() {
        const platformCounts = {};
        this.usernames.forEach(item => {
            platformCounts[item.platform] = (platformCounts[item.platform] || 0) + 1;
        });

        return {
            total: this.usernames.length,
            platforms: platformCounts,
            oldest: this.usernames.length > 0 ? this.usernames[0].timestamp : null,
            newest: this.usernames.length > 0 ? this.usernames[this.usernames.length - 1].timestamp : null
        };
    }

    /**
     * Save usernames to CSV file
     */
    saveToCSV() {
        try {
            // Read existing CSV content (skip header)
            let existingLines = [];
            if (fs.existsSync(this.csvFilePath)) {
                const existingContent = fs.readFileSync(this.csvFilePath, 'utf8');
                existingLines = existingContent.split('\n').filter(line => line.trim() && !line.startsWith('timestamp'));
            }

            // Get new entries that aren't already in CSV
            const existingEntries = new Set(
                existingLines.map(line => {
                    const parts = line.split(',');
                    if (parts.length >= 3) {
                        return `${parts[1]}_${parts[2]}`; // username_platform
                    }
                    return null;
                }).filter(Boolean)
            );

            // Prepare new entries to append
            const newEntries = this.usernames
                .filter(entry => {
                    const key = `${entry.username}_${entry.platform}`;
                    return !existingEntries.has(key);
                })
                .map(entry => {
                    // Escape commas and quotes in CSV
                    const escapeCSV = (str) => {
                        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                            return `"${str.replace(/"/g, '""')}"`;
                        }
                        return str;
                    };
                    return `${entry.timestamp},${escapeCSV(entry.username)},${escapeCSV(entry.platform)}`;
                });

            // Append new entries to CSV
            if (newEntries.length > 0) {
                const content = newEntries.join('\n') + '\n';
                fs.appendFileSync(this.csvFilePath, content, 'utf8');
                console.log(`[UsernameStorage] Saved ${newEntries.length} new entries to CSV`);
            }

            return { saved: newEntries.length };
        } catch (error) {
            console.error(`[UsernameStorage] Error saving to CSV: ${error.message}`);
            return { saved: 0, error: error.message };
        }
    }

    /**
     * Start auto-save interval
     */
    startAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }

        this.autoSaveInterval = setInterval(() => {
            if (this.usernames.length > 0) {
                this.saveToCSV();
            }
        }, this.autoSaveIntervalMs);

        console.log(`[UsernameStorage] Auto-save enabled (every ${this.autoSaveIntervalMs / 1000} seconds)`);
    }

    /**
     * Stop auto-save interval
     */
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }

    /**
     * Clear all stored usernames (in-memory only, CSV is preserved)
     */
    clear() {
        const count = this.usernames.length;
        this.usernames = [];
        console.log(`[UsernameStorage] Cleared ${count} entries from memory`);
        return count;
    }
}

module.exports = UsernameStorage;
