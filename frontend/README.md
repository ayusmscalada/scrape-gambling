# Enrichment Dashboard Frontend

React frontend for viewing enrichment data with real-time WebSocket updates.

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm start
```

The app will run on http://localhost:3000

## Environment Variables

Create a `.env` file:

```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_WS_URL=http://localhost:5000
```

## Features

- Real-time updates via WebSocket
- Three data tables: Raw Players, Qualified Leads, Identity Matches
- Statistics dashboard
- Notification center
- Modern UI with dark theme
