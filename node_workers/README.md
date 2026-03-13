# Puppeteer Workers Service

Node.js HTTP API service for managing Puppeteer browser automation workers.

## Overview

This service provides a REST API for the Python console server to control browser automation for gambling platform scrapers. Each site gets its own isolated Chrome profile and browser instance.

## Architecture

- **server.js**: Express HTTP API server
- **browserManager.js**: Core browser lifecycle management
- **workers/**: Site-specific Puppeteer worker modules (stubs for now)

## API Endpoints

### Health Check
```
GET /health
```

### Get Status
```
GET /status              # All workers
GET /status/:site        # Specific worker
```

### Control Workers
```
POST /start/:site        # Start worker (body: config JSON)
POST /stop/:site         # Stop worker
POST /restart/:site      # Restart worker (body: config JSON)
POST /stop-all           # Stop all workers
```

## Cloudflare "Verify you are human" (Stake, etc.)

If a site shows Cloudflare’s Turnstile challenge, the Stake worker can solve it via [2captcha](https://2captcha.com/).

1. Get a 2captcha API key and add it to your environment:
   - **Docker:** In `.env` set `TWO_CAPTCHA_API_KEY=your_key` (puppeteer-service reads it).
   - **Local Node:** `export TWO_CAPTCHA_API_KEY=your_key` before starting the service.
2. Start the Stake worker as usual; if the challenge appears, the worker will request a token from 2captcha and inject it. Solving takes ~15–30 seconds and uses 2captcha balance.

If `TWO_CAPTCHA_API_KEY` is not set, the challenge is not solved and the worker continues without it.

## Configuration

Workers are configured via the request body when starting:

```json
{
  "headless": false,
  "url": "https://stake.com",
  "profile_dir": "./profiles/stake",
  "viewport_width": 1440,
  "viewport_height": 900,
  "timeout_seconds": 30
}
```

## Running

### In Docker (via docker-compose)
The service runs automatically as part of `docker compose up`.

### Locally
```bash
cd node_workers
npm install
npm start
```

The service listens on port 3000 by default.

## Browser Profiles

Each site maintains its own persistent Chrome profile in `./profiles/<site_key>/`. This ensures:
- Cookies and sessions persist
- Local storage is maintained
- Each site has isolated browser state

## Development

To add site-specific automation logic, edit the corresponding file in `workers/`:

```javascript
// workers/stake.js
module.exports = {
    siteKey: 'stake',
    siteName: 'Stake',
    siteUrl: 'https://stake.com',
    
    async bootstrap(page) {
        // Site-specific initialization
        await page.waitForSelector('.some-element');
    },
    
    async run(page, stopSignal) {
        // Main scraping loop
        while (!stopSignal.isSet) {
            // Collect data, monitor feeds, etc.
            await require('../utils').sleep(5000);
        }
    },
};
```
