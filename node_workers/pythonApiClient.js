/**
 * Python API client for sending user data to Python server
 * Replaces direct PostgreSQL connection
 */

class PythonApiClient {
    constructor(config = {}) {
        this.apiUrl = config.apiUrl || process.env.PYTHON_API_URL || 'http://localhost:5000';
        this.syncInterval = null;
        this.syncIntervalMs = config.intervalMs || 30000; // Default: 30 seconds
        this.lastSyncedTimestamp = null;
        this.usernameStorage = config.usernameStorage;
        
        if (!this.usernameStorage) {
            throw new Error('PythonApiClient requires usernameStorage instance');
        }
        
        console.log(`[PythonApiClient] Initialized with API URL: ${this.apiUrl}`);
    }

    /**
     * Test API connection
     */
    async testConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                console.log('[PythonApiClient] API connection successful');
                return true;
            } else {
                console.error('[PythonApiClient] API health check failed:', response.status);
                return false;
            }
        } catch (error) {
            console.error('[PythonApiClient] API connection failed:', error.message);
            return false;
        }
    }

    /**
     * Send usernames to Python API
     */
    async syncUsernames() {
        try {
            // Get all usernames from storage
            const allUsernames = this.usernameStorage.getUsernames();
            
            if (allUsernames.length === 0) {
                console.log('[PythonApiClient] No usernames to sync');
                return { synced: 0, skipped: 0, errors: 0 };
            }

            // Filter usernames that haven't been synced yet
            let usernamesToSync = allUsernames;
            if (this.lastSyncedTimestamp) {
                usernamesToSync = allUsernames.filter(
                    entry => new Date(entry.timestamp) > new Date(this.lastSyncedTimestamp)
                );
            }

            if (usernamesToSync.length === 0) {
                console.log('[PythonApiClient] No new usernames to sync');
                return { synced: 0, skipped: 0, errors: 0 };
            }

            console.log(`[PythonApiClient] Sending ${usernamesToSync.length} usernames to Python API...`);

            // Format usernames for API
            const players = usernamesToSync.map(entry => ({
                username: entry.username,
                platform: entry.platform,
                timestamp: entry.timestamp
            }));

            // Send to Python API
            const response = await fetch(`${this.apiUrl}/api/raw-players`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ players: players }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API request failed: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Unknown API error');
            }

            // Update last synced timestamp
            if (usernamesToSync.length > 0) {
                const latestTimestamp = usernamesToSync.reduce((latest, entry) => {
                    return new Date(entry.timestamp) > new Date(latest) ? entry.timestamp : latest;
                }, usernamesToSync[0].timestamp);
                this.lastSyncedTimestamp = latestTimestamp;
            }

            console.log(`[PythonApiClient] Sync complete: ${result.inserted} inserted, ${result.skipped} skipped, ${result.errors} errors`);
            
            return {
                synced: result.inserted || 0,
                skipped: result.skipped || 0,
                errors: result.errors || 0
            };
            
        } catch (error) {
            console.error('[PythonApiClient] Error during sync:', error.message);
            return { synced: 0, skipped: 0, errors: 1 };
        }
    }

    /**
     * Start automatic syncing on interval
     */
    startAutoSync() {
        if (this.syncInterval) {
            console.log('[PythonApiClient] Auto-sync already running');
            return;
        }

        console.log(`[PythonApiClient] Starting auto-sync (interval: ${this.syncIntervalMs / 1000} seconds)`);
        
        // Test connection first
        this.testConnection().catch(err => {
            console.error('[PythonApiClient] Connection test failed:', err.message);
        });
        
        // Do initial sync immediately
        this.syncUsernames().catch(err => {
            console.error('[PythonApiClient] Initial sync failed:', err.message);
        });

        // Then sync on interval
        this.syncInterval = setInterval(() => {
            this.syncUsernames().catch(err => {
                console.error('[PythonApiClient] Interval sync failed:', err.message);
            });
        }, this.syncIntervalMs);
    }

    /**
     * Stop automatic syncing
     */
    stopAutoSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
            console.log('[PythonApiClient] Auto-sync stopped');
        }
    }

    /**
     * Manually trigger a sync
     */
    async manualSync() {
        return await this.syncUsernames();
    }
}

module.exports = PythonApiClient;
