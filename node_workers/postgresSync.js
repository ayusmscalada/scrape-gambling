/**
 * PostgreSQL synchronization module
 * Syncs scraped usernames from usernameStorage to PostgreSQL raw_players table
 */

const { Pool } = require('pg');

class PostgresSync {
    constructor(usernameStorage, config = {}) {
        this.usernameStorage = usernameStorage;
        this.syncInterval = null;
        this.syncIntervalMs = config.intervalMs || 30000; // Default: 30 seconds
        this.lastSyncedTimestamp = null;
        
        // PostgreSQL connection pool
        this.pool = new Pool({
            host: config.host || process.env.POSTGRES_HOST || 'postgres',
            port: config.port || parseInt(process.env.POSTGRES_PORT || '5432'),
            database: config.database || process.env.POSTGRES_DB || 'enrichment_db',
            user: config.user || process.env.POSTGRES_USER || 'enrichment_user',
            password: config.password || process.env.POSTGRES_PASSWORD || 'enrichment_pass',
            max: 5, // Maximum number of clients in the pool
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 5000,
        });

        // Handle pool errors
        this.pool.on('error', (err) => {
            console.error('[PostgresSync] Unexpected error on idle client:', err);
        });

        // Test connection on initialization
        this.testConnection();
    }

    /**
     * Test PostgreSQL connection
     */
    async testConnection() {
        try {
            const client = await this.pool.connect();
            const result = await client.query('SELECT NOW()');
            client.release();
            console.log('[PostgresSync] PostgreSQL connection successful');
            return true;
        } catch (error) {
            console.error('[PostgresSync] PostgreSQL connection failed:', error.message);
            return false;
        }
    }

    /**
     * Sync usernames from usernameStorage to PostgreSQL
     * Only syncs new entries since last sync
     */
    async syncUsernames() {
        try {
            // Get all usernames from storage
            const allUsernames = this.usernameStorage.getUsernames();
            
            if (allUsernames.length === 0) {
                console.log('[PostgresSync] No usernames to sync');
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
                console.log('[PostgresSync] No new usernames to sync');
                return { synced: 0, skipped: 0, errors: 0 };
            }

            console.log(`[PostgresSync] Syncing ${usernamesToSync.length} usernames to PostgreSQL...`);

            const client = await this.pool.connect();
            let synced = 0;
            let skipped = 0;
            let errors = 0;

            try {
                // Use a transaction for batch insert
                await client.query('BEGIN');

                // First, check which usernames already exist in the database
                // Check for existing (username, source_site) combinations to avoid duplicates
                const existingSet = new Set();
                
                // Process in batches to avoid query size limits
                const batchSize = 100;
                for (let i = 0; i < usernamesToSync.length; i += batchSize) {
                    const batch = usernamesToSync.slice(i, i + batchSize);
                    
                    // Build VALUES clause for this batch
                    const valuesClause = batch
                        .map((_, idx) => `($${idx * 2 + 1}, $${idx * 2 + 2})`)
                        .join(', ');
                    
                    const checkQuery = `
                        SELECT username, source_site 
                        FROM raw_players 
                        WHERE (username, source_site) IN (VALUES ${valuesClause})
                    `;
                    
                    const checkParams = batch.flatMap(entry => [entry.username, entry.platform]);
                    
                    try {
                        const existingRecords = await client.query(checkQuery, checkParams);
                        existingRecords.rows.forEach(row => {
                            existingSet.add(`${row.username}::${row.source_site || ''}`);
                        });
                    } catch (error) {
                        // If batch check fails, check individually for this batch
                        console.warn(`[PostgresSync] Batch check failed for batch ${i / batchSize + 1}, using individual checks: ${error.message}`);
                        for (const entry of batch) {
                            try {
                                const checkResult = await client.query(
                                    'SELECT 1 FROM raw_players WHERE username = $1 AND source_site = $2 LIMIT 1',
                                    [entry.username, entry.platform]
                                );
                                if (checkResult.rows.length > 0) {
                                    existingSet.add(`${entry.username}::${entry.platform || ''}`);
                                }
                            } catch (err) {
                                // Continue with next entry
                            }
                        }
                    }
                }

                // Prepare insert statement
                const insertQuery = `
                    INSERT INTO raw_players (username, source_site, captured_at)
                    VALUES ($1, $2, $3::timestamptz)
                    RETURNING id
                `;

                // Insert only new entries (skip duplicates)
                for (const entry of usernamesToSync) {
                    try {
                        const key = `${entry.username}::${entry.platform || ''}`;
                        
                        // Skip if already exists in database
                        if (existingSet.has(key)) {
                            skipped++;
                            continue;
                        }

                        const result = await client.query(insertQuery, [
                            entry.username,
                            entry.platform, // source_site in the database
                            entry.timestamp
                        ]);

                        if (result.rowCount > 0) {
                            synced++;
                            // Add to existing set to avoid duplicates within this batch
                            existingSet.add(key);
                        }
                    } catch (error) {
                        // Handle unique constraint violations (if constraint exists)
                        if (error.code === '23505') { // PostgreSQL unique violation
                            skipped++;
                        } else {
                            console.error(`[PostgresSync] Error inserting username ${entry.username}:`, error.message);
                            errors++;
                        }
                    }
                }

                await client.query('COMMIT');
                
                // Update last synced timestamp
                if (usernamesToSync.length > 0) {
                    const latestTimestamp = usernamesToSync.reduce((latest, entry) => {
                        return new Date(entry.timestamp) > new Date(latest) ? entry.timestamp : latest;
                    }, usernamesToSync[0].timestamp);
                    this.lastSyncedTimestamp = latestTimestamp;
                }

                console.log(`[PostgresSync] Sync complete: ${synced} inserted, ${skipped} skipped (duplicates), ${errors} errors`);
                
                return { synced, skipped, errors };
            } catch (error) {
                await client.query('ROLLBACK');
                throw error;
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('[PostgresSync] Error during sync:', error.message);
            return { synced: 0, skipped: 0, errors: 1 };
        }
    }

    /**
     * Start automatic syncing on interval
     */
    startAutoSync() {
        if (this.syncInterval) {
            console.log('[PostgresSync] Auto-sync already running');
            return;
        }

        console.log(`[PostgresSync] Starting auto-sync (interval: ${this.syncIntervalMs / 1000} seconds)`);
        
        // Do initial sync immediately
        this.syncUsernames().catch(err => {
            console.error('[PostgresSync] Initial sync failed:', err.message);
        });

        // Then sync on interval
        this.syncInterval = setInterval(() => {
            this.syncUsernames().catch(err => {
                console.error('[PostgresSync] Interval sync failed:', err.message);
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
            console.log('[PostgresSync] Auto-sync stopped');
        }
    }

    /**
     * Manually trigger a sync
     */
    async manualSync() {
        return await this.syncUsernames();
    }

    /**
     * Close database connection pool
     */
    async close() {
        this.stopAutoSync();
        await this.pool.end();
        console.log('[PostgresSync] Database connection pool closed');
    }
}

module.exports = PostgresSync;
