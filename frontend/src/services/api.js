import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchRawPlayers = async (limit = 100, offset = 0) => {
  const response = await api.get('/api/raw-players', {
    params: { limit, offset },
  });
  return response.data;
};

export const fetchQualifiedLeads = async (limit = 100, offset = 0) => {
  const response = await api.get('/api/qualified-leads', {
    params: { limit, offset },
  });
  return response.data;
};

export const fetchIdentityMatches = async (rawPlayerId = null, limit = 100, offset = 0) => {
  const params = { limit, offset };
  if (rawPlayerId) {
    params.raw_player_id = rawPlayerId;
  }
  const response = await api.get('/api/identity-matches', { params });
  return response.data;
};

export const fetchStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};
