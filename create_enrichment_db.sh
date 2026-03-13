#!/usr/bin/env bash
set -euo pipefail

DB_NAME="enrichment_db"
DB_USER="enrichment_user"
DB_PASS="enrichment_pass"

echo "Creating PostgreSQL user and database..."

# Create user if it does not exist
sudo -u postgres psql -v ON_ERROR_STOP=1 -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}';"

# Create database if it does not exist
sudo -u postgres psql -v ON_ERROR_STOP=1 -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# Grant privileges
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

echo "Done."
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"