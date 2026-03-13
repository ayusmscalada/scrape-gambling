#!/bin/bash
# Fix permissions for profiles directory

echo "🔧 Fixing profiles directory permissions..."

# Get current user ID
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

echo "Current user: $CURRENT_UID:$CURRENT_GID"

# Create profiles directory if it doesn't exist
if [ ! -d "profiles" ]; then
    echo "Creating profiles directory..."
    mkdir -p profiles
fi

# Fix ownership (requires sudo)
echo "Fixing ownership (requires sudo)..."
sudo chown -R $CURRENT_UID:$CURRENT_GID profiles

# Fix permissions
echo "Fixing permissions..."
chmod -R 755 profiles

echo "✅ Profiles directory permissions fixed!"
echo ""
echo "Directory info:"
ls -la profiles | head -5
