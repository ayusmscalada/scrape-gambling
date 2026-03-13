#!/bin/bash
# Diagnostic script to check X11 forwarding setup

echo "=========================================="
echo "X11 Forwarding Diagnostic"
echo "=========================================="
echo ""

# Check 1: Host DISPLAY
echo "1. Checking host DISPLAY variable..."
if [ -z "$DISPLAY" ]; then
    echo "   ❌ DISPLAY is not set on host"
    echo "   Fix: export DISPLAY=:0"
else
    echo "   ✓ DISPLAY is set to: $DISPLAY"
fi

# Check 2: xhost configuration
echo ""
echo "2. Checking xhost configuration..."
if command -v xhost &> /dev/null; then
    xhost_output=$(xhost 2>&1)
    if echo "$xhost_output" | grep -q "LOCAL"; then
        echo "   ✓ xhost allows local connections"
    else
        echo "   ⚠️  xhost may not be configured for Docker"
        echo "   Fix: xhost +local:docker"
    fi
else
    echo "   ❌ xhost command not found"
fi

# Check 3: X11 socket
echo ""
echo "3. Checking X11 socket..."
if [ -d "/tmp/.X11-unix" ]; then
    echo "   ✓ X11 socket directory exists"
    socket_count=$(ls -1 /tmp/.X11-unix/ 2>/dev/null | wc -l)
    echo "   Found $socket_count X11 socket(s)"
else
    echo "   ❌ X11 socket directory not found"
fi

# Check 4: Docker container DISPLAY
echo ""
echo "4. Checking DISPLAY in Docker container..."
if sudo docker compose ps app | grep -q "Up"; then
    container_display=$(sudo docker compose exec app env | grep DISPLAY || echo "NOT SET")
    if [ "$container_display" != "NOT SET" ]; then
        echo "   ✓ DISPLAY in container: $container_display"
    else
        echo "   ❌ DISPLAY not set in container"
        echo "   Check docker-compose.yml environment section"
    fi
else
    echo "   ⚠️  Container is not running"
    echo "   Start it with: sudo docker compose up -d app"
fi

# Check 5: xdpyinfo in container
echo ""
echo "5. Testing xdpyinfo in container..."
if sudo docker compose ps app | grep -q "Up"; then
    if sudo docker compose exec app which xdpyinfo &> /dev/null; then
        echo "   ✓ xdpyinfo is installed"
        echo "   Testing X11 connection..."
        if sudo docker compose exec app xdpyinfo &> /dev/null; then
            echo "   ✓ X11 forwarding is WORKING!"
            xdpyinfo_output=$(sudo docker compose exec app xdpyinfo 2>&1 | head -5)
            echo "   Display info:"
            echo "$xdpyinfo_output" | sed 's/^/      /'
        else
            echo "   ❌ X11 forwarding is NOT working"
            echo "   Error details:"
            sudo docker compose exec app xdpyinfo 2>&1 | head -3 | sed 's/^/      /'
        fi
    else
        echo "   ❌ xdpyinfo is not installed"
        echo "   Rebuild container: sudo docker compose build app"
    fi
else
    echo "   ⚠️  Container is not running"
fi

# Check 6: Worker configuration
echo ""
echo "6. Checking worker configuration..."
if [ -f "config/sites.yaml" ]; then
    headless_count=$(grep -c "headless: true" config/sites.yaml || echo "0")
    headful_count=$(grep -c "headless: false" config/sites.yaml || echo "0")
    echo "   Headless workers: $headless_count"
    echo "   Headful workers: $headful_count"
    if [ "$headless_count" -gt 0 ] && [ "$headful_count" -eq 0 ]; then
        echo "   ⚠️  All workers are configured as headless!"
        echo "   Fix: Set headless: false in config/sites.yaml"
    fi
else
    echo "   ⚠️  config/sites.yaml not found"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "To see browser windows, you need:"
echo "  1. DISPLAY set on host: export DISPLAY=:0"
echo "  2. xhost configured: xhost +local:docker"
echo "  3. DISPLAY passed to container (in docker-compose.yml)"
echo "  4. X11 socket mounted (in docker-compose.yml)"
echo "  5. headless: false in config/sites.yaml"
echo "  6. Container rebuilt with X11 utilities"
echo ""
echo "Quick fix commands:"
echo "  xhost +local:docker"
echo "  export DISPLAY=:0"
echo "  sudo docker compose up -d app"
echo "  sudo docker compose exec app xdpyinfo"
echo ""
