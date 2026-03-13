FROM node:18-slim

WORKDIR /app

# Install system dependencies for Puppeteer/Chromium
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxss1 \
    # X11 client libraries and utilities
    xauth \
    x11-utils \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install Node dependencies (this will also install Chromium via Puppeteer)
# Note: Installing as root, then we'll change ownership
RUN npm install

# Copy application code
COPY . .

# Create profiles directory (will be mounted as volume, but ensure it exists)
RUN mkdir -p /app/profiles

# Expose API port
EXPOSE 3000

# Start server
CMD ["node", "server.js"]
