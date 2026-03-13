#!/bin/bash
# Setup script for X11 forwarding in Docker

set -e

echo "=========================================="
echo "X11 Forwarding Setup for Docker"
echo "=========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges"
    echo "Please run: sudo ./setup_x11.sh"
    exit 1
fi

# Check if DISPLAY is set
if [ -z "$DISPLAY" ]; then
    echo "⚠️  DISPLAY environment variable is not set"
    echo "Setting DISPLAY=:0 (default)"
    export DISPLAY=:0
else
    echo "✓ DISPLAY is set to: $DISPLAY"
fi

# Check if X server is running
if ! pgrep -x "Xorg" > /dev/null && ! pgrep -x "X" > /dev/null; then
    echo "⚠️  Warning: X server doesn't appear to be running"
    echo "   Make sure you're in a graphical session"
else
    echo "✓ X server is running"
fi

# Check X11 socket
if [ -d "/tmp/.X11-unix" ]; then
    echo "✓ X11 socket directory exists"
    # Check permissions
    if [ -r "/tmp/.X11-unix" ]; then
        echo "✓ X11 socket is readable"
    else
        echo "⚠️  X11 socket may not be readable"
        echo "   Trying to fix permissions..."
        chmod 1777 /tmp/.X11-unix 2>/dev/null || true
    fi
else
    echo "❌ X11 socket directory not found"
    echo "   Make sure X server is running"
    exit 1
fi

# Configure xhost
echo ""
echo "Configuring xhost for Docker access..."
echo "   (This allows Docker containers to access your display)"

# Get current user ID
CURRENT_UID=$(id -u)
CURRENT_USER=$(whoami)

# Try to allow Docker access
if command -v xhost &> /dev/null; then
    # Allow local Docker containers
    xhost +local:docker 2>/dev/null || {
        echo "⚠️  Could not run xhost +local:docker"
        echo "   Trying alternative: xhost +SI:localuser:${CURRENT_USER}"
        xhost +SI:localuser:${CURRENT_USER} 2>/dev/null || {
            echo "⚠️  Could not configure xhost"
            echo "   You may need to run manually:"
            echo "   xhost +local:docker"
            echo "   or"
            echo "   xhost +SI:localuser:${CURRENT_USER}"
        }
    }
    echo "✓ Configured xhost for Docker (user ${CURRENT_USER}, UID ${CURRENT_UID})"
else
    echo "⚠️  xhost command not found"
    echo "   Install x11-xserver-utils: sudo apt-get install x11-xserver-utils"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed"
else
    echo "❌ Docker is not installed"
    exit 1
fi

# Check docker-compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "✓ Docker Compose is available"
else
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Rebuild Docker container:"
echo "   sudo docker compose build app"
echo ""
echo "2. Restart containers:"
echo "   sudo docker compose restart app"
echo ""
echo "3. Test X11 forwarding:"
echo "   sudo docker compose exec app xdpyinfo"
echo ""
echo "4. Run the server:"
echo "   sudo docker compose exec app python run_server.py"
echo ""
echo "Then try: automation> start stake"
echo ""
