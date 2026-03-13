#!/bin/bash
# Docker cleanup script - removes containers, images, volumes, and networks

set -e

echo "=========================================="
echo "Docker Cleanup Script"
echo "=========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges"
    echo "Please run: sudo ./cleanup_docker.sh"
    exit 1
fi

echo "This will remove:"
echo "  - All stopped containers"
echo "  - All containers (running and stopped)"
echo "  - All images"
echo "  - All unused volumes"
echo "  - All unused networks"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🧹 Cleaning up Docker resources..."

# Stop all running containers
echo "1. Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "   No running containers to stop"

# Remove all containers
echo "2. Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "   No containers to remove"

# Remove all images
echo "3. Removing all images..."
docker rmi $(docker images -q) 2>/dev/null || echo "   No images to remove"

# Remove unused volumes
echo "4. Removing unused volumes..."
docker volume prune -f

# Remove unused networks
echo "5. Removing unused networks..."
docker network prune -f

# Optional: System prune (removes everything unused)
echo "6. Running system prune (removes all unused resources)..."
docker system prune -a -f --volumes

echo ""
echo "✅ Docker cleanup complete!"
echo ""
echo "To verify:"
echo "  docker ps -a    # Should show no containers"
echo "  docker images   # Should show no images"
echo "  docker volume ls # Should show no volumes (or only system volumes)"
