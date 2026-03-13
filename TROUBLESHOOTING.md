# Troubleshooting Guide

## Puppeteer Service Connection Issues

### Error: "Temporary failure in name resolution"

This error means the Python app cannot connect to the Puppeteer service.

### Solutions

#### 1. Check if Puppeteer service is running

```bash
# Check container status
sudo docker compose ps puppeteer-service

# Check service logs
sudo docker compose logs puppeteer-service

# Check if service is responding
curl http://localhost:3000/health
```

#### 2. Rebuild and start the service

```bash
# Rebuild the Puppeteer service
sudo docker compose build puppeteer-service

# Start the service
sudo docker compose up -d puppeteer-service

# Check logs
sudo docker compose logs -f puppeteer-service
```

#### 3. Verify Docker networking

Both containers must be on the same network:

```bash
# Check networks
sudo docker network inspect scrape-gambling_enrichment_network

# Verify both containers are on the network
sudo docker inspect enrichment_app | grep -A 10 Networks
sudo docker inspect enrichment_puppeteer | grep -A 10 Networks
```

#### 4. Test connection from Python container

```bash
# Enter Python container
sudo docker compose exec app bash

# Test DNS resolution
nslookup puppeteer-service

# Test HTTP connection
curl http://puppeteer-service:3000/health
```

#### 5. Check Node.js dependencies

The Puppeteer service needs Node.js dependencies installed:

```bash
# Check if node_modules exists in container
sudo docker compose exec puppeteer-service ls -la /app/node_modules

# If missing, rebuild
sudo docker compose build puppeteer-service
```

#### 6. Common Issues

**Issue**: Service starts but immediately crashes
- **Solution**: Check logs for errors: `sudo docker compose logs puppeteer-service`
- **Common causes**: Missing dependencies, port conflicts, permission issues

**Issue**: Service is running but not responding
- **Solution**: Check if port 3000 is accessible: `curl http://localhost:3000/health`
- **Check**: Verify healthcheck is passing: `sudo docker compose ps`

**Issue**: DNS resolution fails
- **Solution**: Restart both containers: `sudo docker compose restart app puppeteer-service`
- **Check**: Verify service name matches in docker-compose.yml

## Quick Fix Script

Run the diagnostic script:

```bash
./check_puppeteer.sh
```

This will:
- Check container status
- Test service health endpoint
- Show recent logs
- Provide troubleshooting steps

## Manual Service Start

If automatic startup fails:

```bash
# 1. Build the service
sudo docker compose build puppeteer-service

# 2. Start the service
sudo docker compose up -d puppeteer-service

# 3. Wait for it to be ready (check logs)
sudo docker compose logs -f puppeteer-service

# 4. Test health endpoint
curl http://localhost:3000/health

# 5. Start Python console server
sudo docker compose exec app python run_server.py
```

## Environment Variables

If you need to change the Puppeteer service URL:

```bash
# In docker-compose.yml or .env
PUPPETEER_SERVICE_URL=http://puppeteer-service:3000
```

Or set in Python container:

```bash
export PUPPETEER_SERVICE_URL=http://puppeteer-service:3000
```
