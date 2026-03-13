/**
 * HTTP API server for Puppeteer browser workers
 * Exposes REST endpoints for Python console server to control browsers
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const BrowserManager = require('./browserManager');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Initialize browser manager
const browserManager = new BrowserManager();

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
        console.error(`[start/${req.params.site}] Error:`, error.message);
        console.error(error.stack);
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

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully...');
    await browserManager.stopAll();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully...');
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
