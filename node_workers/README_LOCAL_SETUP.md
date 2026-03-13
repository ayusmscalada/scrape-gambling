# Local Development Setup for Node Workers

This guide explains how to run the Node.js workers service locally (outside Docker).

## Prerequisites

1. **Node.js 24+** installed locally
2. **PostgreSQL** running (either locally or in Docker)
3. **npm** or **yarn** package manager

## Setup Steps

### 1. Install Dependencies

```bash
cd node_workers
npm install
```

This will install:
- `express` - Web server
- `puppeteer` - Browser automation
- `pg` - PostgreSQL client
- `dotenv` - Environment variable loader
- Other dependencies

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL connection details:

```bash
# PostgreSQL Connection
POSTGRES_HOST=localhost        # Use 'localhost' for local, 'postgres' for Docker
POSTGRES_PORT=5433            # Docker mapped port, or 5432 for local PostgreSQL
POSTGRES_DB=enrichment_db
POSTGRES_USER=enrichment_user
POSTGRES_PASSWORD=enrichment_pass

# Sync interval (milliseconds)
POSTGRES_SYNC_INTERVAL_MS=30000

# Server port
PORT=3000
```

### 3. Install Puppeteer Browser

Puppeteer needs to download Chromium:

```bash
cd node_workers
npx puppeteer install chrome
```

Or if you prefer to use system Chrome:

```bash
# Set environment variable to use system Chrome
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome
```

### 4. Start PostgreSQL (if using Docker)

If PostgreSQL is running in Docker:

```bash
# From project root
docker compose up -d postgres

# Verify it's running
docker compose ps postgres
```

### 5. Run the Server

```bash
cd node_workers
npm start
```

Or for development with auto-reload (if using nodemon):

```bash
npm run dev
```

## Verification

### Check Server is Running

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{"status":"ok","service":"puppeteer-workers"}
```

### Check PostgreSQL Connection

The server will log:
```
[PostgresSync] PostgreSQL connection successful
```

If you see an error, check:
1. PostgreSQL is running
2. Connection details in `.env` are correct
3. Network connectivity (if using Docker PostgreSQL)

### Test Username Storage

```bash
# Submit a test username
curl -X POST http://localhost:3000/usernames \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "platform": "stake"}'

# Check stats
curl http://localhost:3000/usernames/stats

# Manually trigger PostgreSQL sync
curl -X POST http://localhost:3000/sync/postgres
```

## Troubleshooting

### PostgreSQL Connection Failed

**Error:** `[PostgresSync] PostgreSQL connection failed`

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   # Docker
   docker compose ps postgres
   
   # Local
   sudo systemctl status postgresql
   ```

2. Check connection details in `.env`:
   - `POSTGRES_HOST` should be `localhost` (not `postgres`)
   - `POSTGRES_PORT` should match your PostgreSQL port (5433 for Docker, 5432 for local)

3. Test connection manually:
   ```bash
   psql -h localhost -p 5433 -U enrichment_user -d enrichment_db
   ```

### Puppeteer Browser Not Found

**Error:** `Could not find Chrome`

**Solutions:**
1. Install Puppeteer browser:
   ```bash
   npx puppeteer install chrome
   ```

2. Or use system Chrome:
   ```bash
   export PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome
   ```

### Port Already in Use

**Error:** `EADDRINUSE: address already in use :::3000`

**Solutions:**
1. Change port in `.env`:
   ```bash
   PORT=3001
   ```

2. Or stop the process using port 3000:
   ```bash
   lsof -ti:3000 | xargs kill
   ```

### Environment Variables Not Loading

Make sure:
1. `.env` file exists in `node_workers/` directory
2. `dotenv` package is installed: `npm install dotenv`
3. Server code loads dotenv: `require('dotenv').config()` at the top

## Development Workflow

1. **Start PostgreSQL** (if using Docker):
   ```bash
   docker compose up -d postgres
   ```

2. **Start Node Workers**:
   ```bash
   cd node_workers
   npm start
   ```

3. **Start Python Console Server** (in another terminal):
   ```bash
   docker compose exec app python run_server.py
   ```

4. **Monitor Logs**:
   - Node workers: Check terminal output
   - PostgreSQL sync: Look for `[PostgresSync]` logs
   - Username storage: Check `/usernames/stats` endpoint

## Environment Variables Reference

| Variable | Default | Description |
|---------|---------|-------------|
| `PORT` | `3000` | Express server port |
| `NODE_ENV` | `development` | Node environment |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5433` | PostgreSQL port |
| `POSTGRES_DB` | `enrichment_db` | Database name |
| `POSTGRES_USER` | `enrichment_user` | Database user |
| `POSTGRES_PASSWORD` | `enrichment_pass` | Database password |
| `POSTGRES_SYNC_INTERVAL_MS` | `30000` | Sync interval (ms) |
| `USERNAME_API_URL` | `http://localhost:3000` | API base URL |
| `DISPLAY` | `:0` | X11 display (for visible browsers) |

## Next Steps

Once the server is running:
1. Start workers via Python console server
2. Workers will scrape usernames
3. Usernames are stored in memory
4. Auto-sync saves to PostgreSQL every 30 seconds
5. Check `raw_players` table in PostgreSQL to verify
