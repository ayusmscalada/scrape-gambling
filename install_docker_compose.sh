#!/usr/bin/env bash
# Install Docker Compose standalone binary when docker-compose-plugin is not in apt.
# Run: sudo ./install_docker_compose.sh
# Then run: ./rebuild_container.sh

set -e
COMPOSE_VERSION="v2.24.5"
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  BINARY="docker-compose-linux-x86_64" ;;
  aarch64|arm64) BINARY="docker-compose-linux-aarch64" ;;
  armv7l|armhf)  BINARY="docker-compose-linux-armv7" ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac
URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/${BINARY}"
echo "Installing Docker Compose ${COMPOSE_VERSION} ($BINARY) to /usr/local/bin/docker-compose"
curl -sSL "$URL" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
/usr/local/bin/docker-compose version
echo "Done. Run ./rebuild_container.sh"
