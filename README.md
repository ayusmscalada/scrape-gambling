# Social Enrichment CLI - Docker + PostgreSQL Setup

Production-style local development environment for social enrichment of gambling platform usernames.

## Services Overview

The Docker Compose setup includes:

- **postgres** - PostgreSQL 15 database (port 5433 on host)
- **app** - Python application container
- **adminer** - Web-based database admin UI (port 8080)

## Quick Start

### 1. Start Services

```bash
# Build and start all services (PostgreSQL + Python app + Adminer)
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 2. Database Monitoring

#### Option A: Adminer (Web UI)

Access the web-based database admin at: **http://localhost:8080**

Login credentials:
- **System:** PostgreSQL
- **Server:** postgres
- **Username:** enrichment_user (or from your .env)
- **Password:** enrichment_pass (or from your .env)
- **Database:** enrichment_db (or from your .env)

#### Option B: Local pgAdmin Application

Connect your local pgAdmin app to the Docker PostgreSQL:

**Connection Settings:**
- **Host:** `localhost`
- **Port:** `5433` ⚠️ (Note: 5433, not 5432)
- **Database:** `enrichment_db`
- **Username:** `enrichment_user`
- **Password:** `enrichment_pass`

See `LOCAL_PGADMIN_CONNECTION.md` for detailed setup instructions.

### 3. Run Database Migrations

```bash
# Initialize Alembic (first time only)
docker compose exec app alembic revision --autogenerate -m "Initial migration"

# Apply migrations
docker compose exec app alembic upgrade head
```

### 4. Run Enrichment

```bash
# Basic usage
docker compose exec app python scan_socials.py antonyambriz

# With source site
docker compose exec app python scan_socials.py antonyambriz --source-site Stake

# With JSON output
docker compose exec app python scan_socials.py antonyambriz --source-site Stake --json-out result.json

# Wait for DB automatically
docker compose exec app python scan_socials.py antonyambriz --wait-db
```

## Project Structure

```
scrape-gambling/
├── scan_socials.py          # CLI entry point
├── app/
│   ├── config.py            # Configuration (environment variables)
│   ├── db/
│   │   ├── base.py          # SQLAlchemy base
│   │   ├── session.py       # Database session management
│   │   ├── models.py        # SQLAlchemy models
│   │   └── repositories.py  # Data access layer
│   └── enrich/
│       ├── normalize.py     # Username normalization
│       ├── search.py        # Platform discovery
│       ├── extract.py       # Evidence extraction
│       ├── score.py         # Confidence scoring
│       ├── classify.py      # Lead classification
│       ├── output.py        # Console/JSON output
│       └── schemas.py        # Data models (Pydantic/dataclasses)
├── alembic/                 # Database migrations
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Database Schema

### raw_players
- Captured usernames from gambling platforms
- One record per enrichment run

### identity_matches
- Discovered social media profiles
- Linked to raw_players via foreign key
- Contains match scores and evidence

### qualified_leads
- Qualified leads (weak/usable only)
- One per raw_player (if applicable)
- Contains best contact information

## Environment Variables

Create a `.env` file:

```bash
POSTGRES_DB=enrichment_db
POSTGRES_USER=enrichment_user
POSTGRES_PASSWORD=enrichment_pass
POSTGRES_HOST=postgres
POSTGRES_PORT=5433  # Default is 5433 to avoid conflicts with local PostgreSQL
ADMINER_PORT=8080   # Port for Adminer web UI (default: 8080)
LOG_LEVEL=INFO
```

**Note:** The Docker container maps to port **5433** on your host by default (to avoid conflicts with local PostgreSQL). The container's internal port is still 5432. If you want to use port 5432, set `POSTGRES_PORT=5432` in your `.env` file and ensure no local PostgreSQL is running.

## Development Commands

```bash
# View logs
docker compose logs -f app

# Access PostgreSQL
docker compose exec postgres psql -U enrichment_user -d enrichment_db

# Run migrations
docker compose exec app alembic upgrade head

# Create new migration
docker compose exec app alembic revision --autogenerate -m "Description"

# Stop services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

## Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_DB=enrichment_db
export POSTGRES_USER=enrichment_user
export POSTGRES_PASSWORD=enrichment_pass

# Run migrations
alembic upgrade head

# Run CLI
python scan_socials.py antonyambriz --source-site Stake
```

## Troubleshooting

### Port 5432 already in use

If you see "address already in use" on port 5432, you have a local PostgreSQL running.

**Option 1: Use different port (recommended)**
```bash
# The default is now 5433 to avoid conflicts
# Just start normally:
docker compose up -d
```

**Option 2: Stop local PostgreSQL**
```bash
# Ubuntu/Debian
sudo systemctl stop postgresql

# macOS (Homebrew)
brew services stop postgresql

# Then start Docker containers
docker compose up -d
```

**Option 3: Use custom port**
```bash
# Set custom port in .env or environment
export POSTGRES_PORT=5434
docker compose up -d
```

### "could not translate host name 'postgres' to address"

This error means the app container can't find the postgres container. Fix it:

```bash
# 1. Check if containers are running
docker compose ps

# 2. If not running, start them
docker compose up -d

# 3. Wait for PostgreSQL to be ready (10-15 seconds)
sleep 10

# 4. Verify containers are on the same network
docker network inspect scrape-gambling_enrichment_network

# 5. Try the migration again
docker compose exec app alembic upgrade head
```

**Quick fix script:**
```bash
./check-containers.sh
docker compose exec app alembic upgrade head
```

### PostgreSQL not ready
Use `--wait-db` flag or wait manually:
```bash
docker compose exec app python scan_socials.py username --wait-db
```

### Migration errors
Reset database (WARNING: deletes all data):
```bash
docker compose down -v
docker compose up -d
sleep 10  # Wait for PostgreSQL
docker compose exec app alembic upgrade head
```

### Connection errors
Check PostgreSQL is running:
```bash
docker compose ps
docker compose logs postgres
docker compose exec postgres pg_isready -U enrichment_user
```

### Using sudo with docker compose
If you need to use `sudo`, ensure containers are started with sudo too:
```bash
sudo docker compose up -d
sudo docker compose exec app alembic upgrade head
```
