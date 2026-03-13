# X11 Forwarding Setup for Visible Browser Windows

This guide explains how to set up X11 forwarding so you can see browser windows when running the automation server in Docker.

## Quick Setup

### 1. Allow X11 Access

On your host machine, run:

```bash
# Allow local connections to X server
xhost +local:docker

# Or more securely, allow only root user from Docker:
xhost +SI:localuser:root
```

**Note:** The less secure `xhost +local:docker` allows any local Docker container to access your display. Use the second command for better security.

### 2. Set DISPLAY Environment Variable

Make sure your `DISPLAY` environment variable is set:

```bash
# Check current DISPLAY
echo $DISPLAY

# If not set, set it (usually :0 or :1)
export DISPLAY=:0
```

### 3. Rebuild and Restart Docker Containers

```bash
# Rebuild the app container with X11 dependencies
sudo docker compose build app

# Restart containers
sudo docker compose down
sudo docker compose up -d

# Or restart just the app container
sudo docker compose restart app
```

### 4. Test X11 Forwarding

```bash
# Test if X11 works in the container
sudo docker compose exec app xeyes

# If xeyes appears, X11 forwarding is working!
# (If xeyes is not installed, install it: sudo apt-get install x11-apps)
```

### 5. Run the Server

```bash
sudo docker compose exec app python run_server.py
```

Then try:
```
automation> start stake
```

You should see a visible Chromium window open!

## Troubleshooting

### "No display server detected"

**Problem:** The container can't access your X server.

**Solutions:**
1. Make sure `xhost` is configured:
   ```bash
   xhost +local:docker
   ```

2. Check DISPLAY is set:
   ```bash
   echo $DISPLAY
   export DISPLAY=:0  # if needed
   ```

3. Verify X11 socket is accessible:
   ```bash
   ls -la /tmp/.X11-unix/
   ```

4. Restart Docker containers after changes:
   ```bash
   sudo docker compose restart app
   ```

### "Cannot connect to X server"

**Problem:** X11 permissions issue.

**Solutions:**
1. Check X11 socket permissions:
   ```bash
   ls -la /tmp/.X11-unix/
   sudo chmod 1777 /tmp/.X11-unix
   ```

2. Try allowing all local connections (less secure):
   ```bash
   xhost +local:
   ```

3. Check if you're running X server:
   ```bash
   ps aux | grep X
   ```

### Browser window doesn't appear

**Problem:** Browser launches but window is not visible.

**Solutions:**
1. Check if browser is actually running:
   ```bash
   sudo docker compose exec app ps aux | grep chromium
   ```

2. Verify DISPLAY in container:
   ```bash
   sudo docker compose exec app env | grep DISPLAY
   ```

3. Check X11 forwarding:
   ```bash
   sudo docker compose exec app xdpyinfo
   ```

### Running on Remote Server

If you're SSH'd into a remote server:

1. **Enable X11 forwarding in SSH:**
   ```bash
   ssh -X username@server
   # or
   ssh -Y username@server  # trusted X11 forwarding
   ```

2. **Set DISPLAY on remote:**
   ```bash
   export DISPLAY=localhost:10.0  # or whatever SSH sets
   ```

3. **Allow X11 forwarding in SSH config:**
   ```
   # In ~/.ssh/config
   Host *
       ForwardX11 yes
       ForwardX11Trusted yes
   ```

## Security Notes

- `xhost +local:docker` allows any Docker container to access your display
- For better security, use `xhost +SI:localuser:root` to only allow root user
- Consider using X11 authentication (xauth) for more secure setups
- On production servers, consider using VNC or a virtual display instead

## Alternative: Use xvfb (Virtual Display)

If you don't need to see the browser windows but want to avoid headless mode issues:

```bash
# Install xvfb in container
sudo docker compose exec app apt-get update
sudo docker compose exec app apt-get install -y xvfb

# Run with virtual display
sudo docker compose exec app xvfb-run -a python run_server.py
```

This creates a virtual X server that browsers can use, but you won't see the windows.

## Verification

After setup, verify everything works:

```bash
# 1. Check DISPLAY is set
echo $DISPLAY

# 2. Check xhost allows Docker
xhost

# 3. Test X11 in container
sudo docker compose exec app xdpyinfo

# 4. Start server and test browser
sudo docker compose exec app python run_server.py
# Then: automation> start stake
```

If all steps work, you should see the browser window!
