#!/bin/bash
# Install Playwright in Docker container

echo "Installing Playwright in Docker container..."
sudo docker compose exec app pip install playwright==1.40.0
sudo docker compose exec app playwright install chromium
echo "Playwright installed successfully!"
