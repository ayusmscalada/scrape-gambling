# Refactor Summary: Playwright → Puppeteer

## Overview

The automation console server has been refactored to use **Puppeteer (Node.js)** instead of **Playwright (Python)** for browser automation.

## Architecture Changes

### Before (Playwright)
- Python console server → Python Playwright workers → Chromium browsers
- All browser automation in Python
- Single container for Python app

### After (Puppeteer)
- Python console server → HTTP API → Node.js Puppeteer service → Chromium browsers
- Browser automation in Node.js
- Two containers: Python app + Puppeteer service

## New Components

### Node.js Puppeteer Service
- **Location**: `node_workers/`
- **Files**:
  - `server.js`: Express HTTP API server
  - `browserManager.js`: Browser lifecycle management
  - `workers/*.js`: Site-specific worker modules (14 sites)
  - `package.json`: Node dependencies
  - `Dockerfile`: Node service container

### Python Puppeteer Client
- **Location**: `app/manager/puppeteer_client.py`
- **Purpose**: HTTP client for communicating with Puppeteer service
- **Methods**: `start_worker()`, `stop_worker()`, `restart_worker()`, `get_status()`, etc.

## Removed Components

### Playwright Dependencies
- ❌ `playwright==1.40.0` from `requirements.txt`
- ❌ Playwright browser installation from `Dockerfile`
- ❌ Playwright system dependencies from `Dockerfile`
- ❌ `app/automations/base.py` (deprecated, no longer used)
- ❌ Site worker classes in `app/automations/*.py` (deprecated)

### Scripts
- ❌ `install_browsers.sh` (no longer needed)
- ❌ `install_playwright.sh` (no longer needed)

## Updated Components

### Python Manager (`app/manager/server.py`)
- Now calls Puppeteer HTTP API instead of creating Playwright workers
- Uses `PuppeteerClient` for all browser operations
- Worker state tracked via API responses

### Registry (`app/manager/registry.py`)
- Simplified to only validate site keys
- No longer creates worker instances (handled by Puppeteer)

### Docker Configuration
- **docker-compose.yml**: Added `puppeteer-service` container
- **Dockerfile**: Removed Playwright installation
- **requirements.txt**: Replaced `playwright` with `httpx`

## API Endpoints

The Puppeteer service exposes:

```
GET  /health              # Health check
GET  /status              # All workers status
GET  /status/:site        # Specific worker status
POST /start/:site         # Start worker (body: config)
POST /stop/:site          # Stop worker
POST /restart/:site       # Restart worker (body: config)
POST /stop-all            # Stop all workers
```

## Usage

### Starting the System

```bash
# Build and start all services
docker compose up --build -d

# Check Puppeteer service health
curl http://localhost:3000/health

# Run console server
docker compose exec app python run_server.py
```

### Console Commands (Unchanged)

```
automation> start stake
automation> stop stake
automation> restart stake
automation> status
automation> start all
automation> stop all
```

Commands work the same, but now control Puppeteer browsers via HTTP API.

## Browser Profiles

Each site maintains its own persistent Chrome profile:
- **Location**: `./profiles/<site_key>/`
- **Mounted**: Shared volume between containers
- **Isolation**: Each site has separate cookies, sessions, local storage

## Configuration

Site configuration remains in `config/sites.yaml`:
- `headless`: Browser visibility
- `url`: Target site URL
- `profile_dir`: Profile directory path
- `viewport_width/height`: Browser viewport size
- `timeout_seconds`: Navigation timeout

## Migration Notes

### For Developers

1. **Adding Site-Specific Logic**: Edit `node_workers/workers/<site>.js`
2. **Browser Automation**: Use Puppeteer API in Node.js workers
3. **Python Integration**: Use `PuppeteerClient` in Python code

### For Users

- Console commands remain the same
- Browser behavior is unchanged (visible/hidden, profiles, etc.)
- No changes to `config/sites.yaml` format

## Benefits

1. **Separation of Concerns**: Browser automation isolated in Node.js
2. **Better Performance**: Puppeteer is optimized for Node.js
3. **Easier Maintenance**: Browser code separate from Python logic
4. **Scalability**: Puppeteer service can be scaled independently

## Troubleshooting

### Puppeteer Service Not Available
```bash
# Check service status
docker compose ps puppeteer-service

# Check logs
docker compose logs puppeteer-service

# Restart service
docker compose restart puppeteer-service
```

### Browser Not Visible
- Ensure X11 forwarding is set up (same as before)
- Check `DISPLAY` environment variable
- Verify X11 socket permissions

### Profile Issues
- Profiles are stored in `./profiles/`
- Each site has its own directory
- Clear profile directory to reset browser state
