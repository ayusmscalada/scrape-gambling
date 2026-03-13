# Connect Local pgAdmin to Docker PostgreSQL

## Connection Details

Use these settings in your local pgAdmin application to connect to the Docker PostgreSQL container:

### Server Connection Settings

**General Tab:**
- **Name:** `Enrichment DB` (or any name you prefer)

**Connection Tab:**
- **Host name/address:** `localhost` or `127.0.0.1`
- **Port:** `5433` ⚠️ (Note: 5433, not 5432 - to avoid conflicts with local PostgreSQL)
- **Maintenance database:** `enrichment_db`
- **Username:** `enrichment_user`
- **Password:** `enrichment_pass`
- ✅ **Save password** (check this box for convenience)

**Advanced Tab (optional):**
- **DB restriction:** Leave empty or specify `enrichment_db` to only show this database

## Step-by-Step Instructions

### 1. Ensure PostgreSQL Container is Running

```bash
sudo docker compose ps postgres
```

If not running:
```bash
sudo docker compose up -d postgres
```

### 2. Verify Port is Exposed

```bash
sudo docker compose ps postgres
# Should show: 0.0.0.0:5433->5432/tcp
```

### 3. Open pgAdmin

Launch your local pgAdmin application.

### 4. Add New Server

1. **Right-click** on "Servers" in the left sidebar
2. Select **"Register" → "Server"**

### 5. Enter Connection Details

**General Tab:**
- Name: `Enrichment DB`

**Connection Tab:**
- Host: `localhost`
- Port: `5433`
- Database: `enrichment_db`
- Username: `enrichment_user`
- Password: `enrichment_pass`

### 6. Test Connection

Click **"Save"** - pgAdmin will test the connection automatically.

If successful, you'll see the server appear in the sidebar with the database expanded.

## Troubleshooting

### Connection Refused

**Check if container is running:**
```bash
sudo docker compose ps postgres
```

**Check if port is exposed:**
```bash
sudo netstat -tulpn | grep 5433
# or
sudo lsof -i :5433
```

**Verify PostgreSQL is ready:**
```bash
sudo docker compose exec postgres pg_isready -U enrichment_user
```

### Wrong Port

If you changed `POSTGRES_PORT` in your `.env` or `docker-compose.yml`, use that port instead of 5433.

**Check actual port:**
```bash
sudo docker compose ps postgres
# Look for the port mapping: 0.0.0.0:XXXX->5432/tcp
```

### Authentication Failed

**Verify credentials:**
```bash
# Check environment variables
sudo docker compose exec postgres env | grep POSTGRES
```

**Default credentials:**
- Username: `enrichment_user`
- Password: `enrichment_pass`
- Database: `enrichment_db`

### Port 5433 Already in Use

If port 5433 is already in use, either:
1. Change the port in `docker-compose.yml`:
   ```yaml
   ports:
     - "5434:5432"  # Use 5434 instead
   ```
2. Or stop the service using port 5433

## Quick Connection String

For reference, the connection string format is:
```
postgresql://enrichment_user:enrichment_pass@localhost:5433/enrichment_db
```

## Verify Connection

Once connected, you should see:
- **Servers** → **Enrichment DB** → **Databases** → **enrichment_db** → **Schemas** → **public** → **Tables**
  - `raw_players`
  - `identity_matches`
  - `qualified_leads`
  - `alembic_version`

## Custom Configuration

If you've customized the database settings in `.env` or `docker-compose.yml`, use those values instead:

```bash
# Check your actual configuration
cat .env | grep POSTGRES
```

Then use those values in pgAdmin.
