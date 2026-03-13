# Prefer standalone docker-compose (works without plugin). Use sudo for same privilege as rest of script.
if sudo /usr/local/bin/docker-compose version &>/dev/null; then
  DCOMPOSE="/usr/local/bin/docker-compose"
elif sudo /usr/bin/docker-compose version &>/dev/null; then
  DCOMPOSE="/usr/bin/docker-compose"
elif sudo docker-compose version &>/dev/null; then
  DCOMPOSE="docker-compose"
else
  # Only use "docker compose" if it really works (some systems print "unknown command" but exit 0)
  out=$(sudo docker compose version 2>&1) || true
  if [[ -n "$out" && "$out" != *"unknown command"* ]] && sudo docker compose version &>/dev/null; then
    DCOMPOSE="docker compose"
  else
    echo "Error: No Docker Compose found."
    echo "  Install the standalone binary (no apt package needed):"
    echo "    sudo ./install_docker_compose.sh"
    echo "  Or add Docker's repo and install the plugin:"
    echo "    https://docs.docker.com/engine/install/ubuntu/"
    exit 1
  fi
fi

# 1. Setup X11 on host (if not already done)
xhost +local:docker
export DISPLAY=:0

# 2. Rebuild container with X11 utilities
sudo $DCOMPOSE build app

# 3. Start/restart container
# Use 'up -d' instead of 'restart' to start if not running
sudo $DCOMPOSE up -d app

# 4. Verify xdpyinfo is installed
sudo $DCOMPOSE exec app which xdpyinfo
# Should output: /usr/bin/xdpyinfo

# 5. Test X11 forwarding
sudo $DCOMPOSE exec app xdpyinfo
# Should show display information if X11 is working

# 6. If xdpyinfo works, run the server
sudo $DCOMPOSE exec app python run_server.py