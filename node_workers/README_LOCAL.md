# Running Puppeteer Service Locally (Without Docker)

## Prerequisites

1. **Node.js 24+** (or 18+ if 24 is not available)
   ```bash
   node --version  # Should be 24.x.x or higher
   ```

2. **npm** (comes with Node.js)
   ```bash
   npm --version
   ```

## Setup Steps

### 1. Navigate to the node_workers directory

```bash
cd node_workers
```

### 2. Install Node.js dependencies

```bash
npm install
```

This will install:
- `puppeteer` - Browser automation
- `express` - HTTP server
- `cors` - CORS middleware
- `body-parser` - JSON body parser

### 3. Install Puppeteer browser

```bash
# Install Chrome (recommended)
npx puppeteer install chrome

# Or install Chromium
npx puppeteer install chromium@latest
```

**Note**: This downloads the browser binary (~200-300MB). It may take a few minutes.

### 4. Create profiles directory

```bash
# From project root
mkdir -p profiles

# Or from node_workers directory
mkdir -p ../profiles
```

### 5. Set environment variables (optional)

```bash
# Set port (default: 3000)
export PORT=3000

# Set Puppeteer cache directory (optional)
export PUPPETEER_CACHE_DIR=~/.cache/puppeteer
```

### 6. Run the server

```bash
# From node_workers directory
npm start

# Or directly
node server.js
```

You should see:
```
Puppeteer workers API server running on port 3000
Health check: http://localhost:3000/health
```

## Testing

### Health Check

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "puppeteer-workers"
}
```

### Start a Browser Worker

```bash
curl -X POST http://localhost:3000/start/stake \
  -H "Content-Type: application/json" \
  -d '{
    "headless": true,
    "url": "https://stake.com",
    "profile_dir": "./profiles/stake"
  }' | python3 -m json.tool
```

### Check Status

```bash
curl http://localhost:3000/status | python3 -m json.tool
```

## Quick Start Script

Create a file `start-local.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")/node_workers"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if browser is installed
if [ ! -d "$HOME/.cache/puppeteer" ]; then
    echo "Installing Puppeteer browser..."
    npx puppeteer install chrome
fi

# Create profiles directory
mkdir -p ../profiles

# Start server
echo "Starting Puppeteer service on port 3000..."
npm start
```

Make it executable and run:
```bash
chmod +x start-local.sh
./start-local.sh
```

## Troubleshooting

### Browser not found

If you see "Could not find Chrome", install it:
```bash
npx puppeteer install chrome
```

### Port already in use

Change the port:
```bash
PORT=3001 node server.js
```

### Permission errors

If you get permission errors with profiles directory:
```bash
chmod -R 755 profiles/
```

### Network issues during browser install

Retry the browser installation:
```bash
npx puppeteer install chrome
```

If it fails, try with a longer timeout:
```bash
PUPPETEER_DOWNLOAD_TIMEOUT=60000 npx puppeteer install chrome
```

## Running in Background

### Using nohup

```bash
nohup node server.js > puppeteer.log 2>&1 &
```

### Using pm2 (recommended for production)

```bash
# Install pm2 globally
npm install -g pm2

# Start service
pm2 start server.js --name puppeteer-service

# Check status
pm2 status

# View logs
pm2 logs puppeteer-service

# Stop service
pm2 stop puppeteer-service
```

## Configuration

The server reads configuration from:
- Environment variables (PORT, PUPPETEER_CACHE_DIR)
- Default values (PORT=3000)

Profiles are stored in: `../profiles/` (relative to node_workers directory)

Browser cache is stored in: `~/.cache/puppeteer` (or PUPPETEER_CACHE_DIR if set)

## Integration with Python Console Server

When running locally, update the Python console server to connect to `localhost:3000`:

```python
# In app/manager/server.py or run_server.py
puppeteer_url = os.environ.get('PUPPETEER_SERVICE_URL', 'http://localhost:3000')
```

Or set environment variable:
```bash
export PUPPETEER_SERVICE_URL=http://localhost:3000
python run_server.py
```
