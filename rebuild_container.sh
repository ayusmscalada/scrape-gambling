# 1. Setup X11 on host (if not already done)
xhost +local:docker
export DISPLAY=:0

# 2. Rebuild container with X11 utilities
sudo docker compose build app

# 3. Start/restart container
# Use 'up -d' instead of 'restart' to start if not running
sudo docker compose up -d app

# 4. Verify xdpyinfo is installed
sudo docker compose exec app which xdpyinfo
# Should output: /usr/bin/xdpyinfo

# 5. Test X11 forwarding
sudo docker compose exec app xdpyinfo
# Should show display information if X11 is working

# 6. If xdpyinfo works, run the server
sudo docker compose exec app python run_server.py