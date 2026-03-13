/**
 * HTTP API server for Puppeteer browser workers
 * Exposes REST endpoints for Python console server to control browsers
 */

// Load environment variables from .env file (if it exists)
require('dotenv').config();

// Set Puppeteer cache directory early (before requiring browserManager)
// This must be set before Puppeteer is loaded
if (!process.env.PUPPETEER_CACHE_DIR) {
    const os = require('os');
    const path = require('path');
    const fs = require('fs');
    const isDocker = fs.existsSync('/.dockerenv');
    const cacheDir = isDocker 
        ? '/app/.puppeteer-cache' 
        : path.join(os.homedir(), '.cache', 'puppeteer');
    process.env.PUPPETEER_CACHE_DIR = cacheDir;
    console.log(`[Server] Set PUPPETEER_CACHE_DIR to: ${cacheDir}`);
}

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const BrowserManager = require('./browserManager');
const UsernameStorage = require('./usernameStorage');
const PythonApiClient = require('./pythonApiClient');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Initialize browser manager
const browserManager = new BrowserManager();

// Initialize username storage
const usernameStorage = new UsernameStorage();

// Initialize Python API client (replaces PostgreSQL sync)
const pythonApiClient = new PythonApiClient({
    usernameStorage: usernameStorage,
    intervalMs: parseInt(process.env.PYTHON_API_SYNC_INTERVAL_MS || '30000'), // Default: 30 seconds
    apiUrl: process.env.PYTHON_API_URL || 'http://localhost:5000',
});

// Start auto-sync to Python API
pythonApiClient.startAutoSync();

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'puppeteer-workers' });
});

// Get status of all workers
app.get('/status', (req, res) => {
    try {
        const status = browserManager.getAllStatus();
        res.json({ success: true, workers: status });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Get status of specific worker
app.get('/status/:site', (req, res) => {
    try {
        const { site } = req.params;
        const status = browserManager.getState(site);
        res.json({ success: true, ...status });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Start a worker
app.post('/start/:site', async (req, res) => {
    try {
        const { site } = req.params;
        const config = req.body || {};
        
        const result = await browserManager.start(site, config);
        res.json(result);
    } catch (error) {
        res.status(500).json({
            success: false,
            site: req.params.site,
            error: error.message,
        });
    }
});

// Stop a worker
app.post('/stop/:site', async (req, res) => {
    try {
        const { site } = req.params;
        const result = await browserManager.stop(site);
        res.json(result);
    } catch (error) {
        res.status(500).json({
            success: false,
            site: req.params.site,
            error: error.message,
        });
    }
});

// Restart a worker
app.post('/restart/:site', async (req, res) => {
    try {
        const { site } = req.params;
        const config = req.body || {};
        
        const result = await browserManager.restart(site, config);
        res.json(result);
    } catch (error) {
        res.status(500).json({
            success: false,
            site: req.params.site,
            error: error.message,
        });
    }
});

// Stop all workers
app.post('/stop-all', async (req, res) => {
    try {
        const results = await browserManager.stopAll();
        res.json({ success: true, results });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// ============================================
// Username Storage Endpoints
// ============================================

// Add usernames (POST /usernames)
// Body: { usernames: [{username: "...", platform: "..."}, ...] }
//   or: { username: "...", platform: "..." } (single entry)
app.post('/usernames', (req, res) => {
    try {
        const body = req.body;
        
        if (body.usernames && Array.isArray(body.usernames)) {
            // Multiple usernames
            const result = usernameStorage.addUsernames(body.usernames);
            res.json({
                success: true,
                added: result.added,
                skipped: result.skipped,
                message: `Added ${result.added} usernames, skipped ${result.skipped} duplicates`
            });
        } else if (body.username && body.platform) {
            // Single username
            const added = usernameStorage.addUsername(body.username, body.platform);
            res.json({
                success: true,
                added: added ? 1 : 0,
                skipped: added ? 0 : 1,
                message: added ? 'Username added' : 'Duplicate username skipped'
            });
        } else {
            res.status(400).json({
                success: false,
                error: 'Invalid request body. Expected {username, platform} or {usernames: [{username, platform}, ...]}'
            });
        }
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get usernames (GET /usernames?platform=...&limit=...)
app.get('/usernames', (req, res) => {
    try {
        const options = {
            platform: req.query.platform || null,
            limit: req.query.limit ? parseInt(req.query.limit) : null
        };
        
        const usernames = usernameStorage.getUsernames(options);
        res.json({
            success: true,
            count: usernames.length,
            usernames: usernames
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get statistics (GET /usernames/stats)
app.get('/usernames/stats', (req, res) => {
    try {
        const stats = usernameStorage.getStats();
        res.json({
            success: true,
            stats: stats
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Manually save to CSV (POST /usernames/save)
app.post('/usernames/save', (req, res) => {
    try {
        const result = usernameStorage.saveToCSV();
        res.json({
            success: true,
            saved: result.saved,
            message: `Saved ${result.saved} entries to CSV`
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// ============================================
// Python API Sync Endpoints
// ============================================

// Manually trigger Python API sync (POST /sync/python-api)
app.post('/sync/python-api', async (req, res) => {
    try {
        const result = await pythonApiClient.manualSync();
        res.json({
            success: true,
            synced: result.synced,
            skipped: result.skipped,
            errors: result.errors,
            message: `Synced ${result.synced} usernames to Python API (${result.skipped} skipped, ${result.errors} errors)`
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully...');
    usernameStorage.saveToCSV();
    usernameStorage.stopAutoSave();
    pythonApiClient.stopAutoSync();
    await pythonApiClient.manualSync(); // Final sync before shutdown
    await browserManager.stopAll();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully...');
    usernameStorage.saveToCSV();
    usernameStorage.stopAutoSave();
    pythonApiClient.stopAutoSync();
    await pythonApiClient.manualSync(); // Final sync before shutdown
    await browserManager.stopAll();
    process.exit(0);
});

// Start server
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Puppeteer workers API server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
});

// Handle server errors
server.on('error', (error) => {
    if (error.syscall !== 'listen') {
        throw error;
    }
    console.error(`Server error: ${error}`);
    process.exit(1);
});
