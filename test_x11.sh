#!/bin/bash
# Test X11 forwarding and browser visibility

echo "=========================================="
echo "X11 and Browser Visibility Test"
echo "=========================================="
echo ""

# Test 1: xdpyinfo
echo "1. Testing xdpyinfo..."
if sudo docker compose exec app xdpyinfo &> /dev/null; then
    echo "   ✓ X11 forwarding is WORKING!"
    echo "   Display information:"
    sudo docker compose exec app xdpyinfo 2>&1 | head -5 | sed 's/^/      /'
else
    echo "   ❌ X11 forwarding is NOT working"
    echo "   Error:"
    sudo docker compose exec app xdpyinfo 2>&1 | head -3 | sed 's/^/      /'
    echo ""
    echo "   Fix:"
    echo "     xhost +local:docker"
    echo "     export DISPLAY=:0"
    echo "     sudo docker compose restart app"
    exit 1
fi

echo ""
echo "2. Checking DISPLAY in container..."
container_display=$(sudo docker compose exec app env | grep DISPLAY)
echo "   $container_display"

echo ""
echo "3. Checking X11 socket permissions..."
sudo docker compose exec app ls -la /tmp/.X11-unix/ | grep -E "X0|X1" | head -2

echo ""
echo "4. Testing if browser can access display..."
echo "   (This will try to launch a headless browser to test connection)"
sudo docker compose exec app python3 -c "
import os
display = os.environ.get('DISPLAY', 'NOT SET')
print(f'   DISPLAY in Python: {display}')
if display != 'NOT SET':
    print('   ✓ DISPLAY is accessible to Python')
else:
    print('   ❌ DISPLAY not accessible to Python')
"

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "If xdpyinfo works above, X11 forwarding is configured correctly."
echo ""
echo "To see browser windows:"
echo "  1. Make sure config/sites.yaml has: headless: false"
echo "  2. Run: sudo docker compose exec app python run_server.py"
echo "  3. Then: automation> start stake"
echo ""
echo "If browser still doesn't appear, check the logs for:"
echo "  - 'Automatically switching to headless mode' (means X11 not detected)"
echo "  - 'Creating persistent context (headless=True' (means running headless)"
echo ""
