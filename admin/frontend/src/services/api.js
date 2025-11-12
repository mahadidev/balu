import axios from 'axios';

// Base API configuration  
const API_BASE_URL = process.env.REACT_APP_API_URL || (window.location.origin + '/api');

console.log("API_BASE_URL",API_BASE_URL);

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
};

// Rooms API
export const roomsApi = {
  getAll: (includeInactive = false) => api.get('/rooms/', { params: { include_inactive: includeInactive } }),
  getById: (id) => api.get(`/rooms/${id}`),
  create: (data) => api.post('/rooms/', data),
  update: (id, data) => api.put(`/rooms/${id}`, data),
  delete: (id) => api.delete(`/rooms/${id}`),
  
  // Permissions
  getPermissions: (id) => api.get(`/rooms/${id}/permissions`),
  updatePermissions: (id, data) => api.put(`/rooms/${id}/permissions`, data),
  
  // Channels
  getChannels: (id) => api.get(`/rooms/${id}/channels`),
  registerChannel: (id, data) => api.post(`/rooms/${id}/channels`, data),
  unregisterChannel: (id, guildId, channelId) => api.delete(`/rooms/${id}/channels/${guildId}/${channelId}`),
};

// Servers API
export const serversApi = {
  getAll: (activeOnly = true) => api.get('/servers/', { params: { active_only: activeOnly } }),
  getById: (guildId) => api.get(`/servers/${guildId}`),
  getChannels: (roomId, guildId) => api.get('/servers/channels', { 
    params: { room_id: roomId, guild_id: guildId } 
  }),
  getStatistics: (guildId, days = 7) => api.get(`/servers/${guildId}/stats`, { params: { days } }),
  getActivity: (guildId, hours = 24) => api.get(`/servers/${guildId}/activity`, { params: { hours } }),
  
  // Bulk operations
  refreshCache: () => api.post('/servers/bulk/refresh-cache'),
  unregisterChannel: (guildId, channelId) => api.delete(`/servers/channels/${guildId}/${channelId}`),
};

// Analytics API
export const analyticsApi = {
  getLiveStats: () => api.get('/analytics/live'),
  getMessageStats: (days = 7) => api.get('/analytics/messages', { params: { days } }),
  getRoomStats: (roomId, days = 7) => api.get(`/analytics/rooms/${roomId}/stats`, { params: { days } }),
  getSystemHealth: () => api.get('/analytics/health'),
  getTrends: (period = 'week') => api.get('/analytics/trends', { params: { period } }),
  getTopGuilds: (days = 7, limit = 10) => api.get('/analytics/top-guilds', { params: { days, limit } }),
  getTopUsers: (days = 7, limit = 10) => api.get('/analytics/top-users', { params: { days, limit } }),
  exportMessages: (params) => api.get('/analytics/export/messages', { params }),
};

// System API
export const systemApi = {
  getStatus: () => api.get('/status'),
  getInfo: () => api.get('/info'),
};

// WebSocket connection helper
export const createWebSocketConnection = (onMessage, onError, onOpen, onClose) => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = (event) => {
    console.log('WebSocket connected');
    
    // Authenticate the connection
    const token = localStorage.getItem('token');
    if (token) {
      ws.send(JSON.stringify({
        type: 'authenticate',
        token: token
      }));
    }
    
    if (onOpen) onOpen(event);
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (error) {
      console.error('WebSocket message parse error:', error);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };
  
  ws.onclose = (event) => {
    console.log('WebSocket disconnected:', event.reason);
    if (onClose) onClose(event);
  };
  
  return ws;
};

export default api;