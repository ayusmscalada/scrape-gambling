# Frontend Setup Guide

## Overview

The React frontend provides a real-time dashboard for viewing:
- **Raw Players**: Scraped usernames from gambling platforms
- **Qualified Leads**: Players with social media matches
- **Identity Matches**: Social media profile matches

## Features

- ✅ Real-time WebSocket updates
- ✅ Modern dark theme UI
- ✅ Three data tables with pagination
- ✅ Statistics dashboard
- ✅ Notification center
- ✅ Responsive design

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:5000
REACT_APP_WS_URL=http://localhost:5000
```

### 3. Start Development Server

```bash
npm start
```

The frontend will run on http://localhost:3000

## Backend Setup

### 1. Install Python Dependencies

```bash
pip install Flask-SocketIO Flask-CORS
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Start Python API Server

```bash
python run_server.py
```

The API server will run on http://localhost:5000

## Architecture

### WebSocket Events

The Python backend emits the following WebSocket events:

- `raw_player_added` - When a new player is scraped
- `qualified_lead_updated` - When a lead is qualified
- `identity_match_added` - When a social match is found
- `stats_updated` - When statistics change

### API Endpoints

- `GET /api/raw-players` - Get raw players (with pagination)
- `GET /api/qualified-leads` - Get qualified leads
- `GET /api/identity-matches` - Get identity matches
- `GET /api/stats` - Get overall statistics
- `POST /api/raw-players` - Receive new players from node_workers

## Usage

1. Start the Python backend: `python run_server.py`
2. Start the React frontend: `cd frontend && npm start`
3. Open http://localhost:3000 in your browser
4. Watch real-time updates as data flows in!

## Production Build

```bash
cd frontend
npm run build
```

The build output will be in `frontend/build/`
