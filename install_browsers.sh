#!/bin/bash
# Install Playwright browsers in Docker container

echo "=========================================="
echo "Installing Playwright browsers in container"
echo "=========================================="
echo ""

echo "Running in Docker container..."
sudo docker compose exec app bash -c "
export PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers
mkdir -p /app/.playwright-browsers
echo 'Installing Chromium...'
playwright install chromium
echo ''
echo 'Browsers installed to: \$PLAYWRIGHT_BROWSERS_PATH'
ls -la /app/.playwright-browsers/ | head -10
echo ''
echo '✅ Installation complete!'
"
