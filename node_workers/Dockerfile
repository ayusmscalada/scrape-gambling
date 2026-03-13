FROM node:24-slim

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

# Set Puppeteer cache directory and skip browser download during npm install
ENV PUPPETEER_CACHE_DIR=/app/.puppeteer-cache
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy package files
COPY package*.json ./

# Install Node dependencies (skip browser download to avoid network issues)
RUN npm install

# Create cache directory before installing browser
RUN mkdir -p /app/.puppeteer-cache

# Now install Chromium browser separately with retries
# Use 'chrome' instead of 'chromium' - Chrome is the pinned browser for Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
RUN npx puppeteer install chrome || \
    (echo "Retry 1..." && sleep 10 && npx puppeteer install chrome) || \
    (echo "Retry 2..." && sleep 20 && npx puppeteer install chrome)

# Make cache directory accessible to all users
RUN chmod -R 777 /app/.puppeteer-cache 2>/dev/null || true

# Copy application code
COPY . .

# Create profiles directory (will be mounted as volume, but ensure it exists)
RUN mkdir -p /app/profiles
RUN chmod 777 /app/profiles

# Expose API port
EXPOSE 3000

# Start server
CMD ["node", "server.js"]
