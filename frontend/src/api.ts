import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
};

// Preferences API
export const preferencesAPI = {
  get: () => api.get('/api/preferences'),
  create: (prefs: any) => api.post('/api/preferences', prefs),
  update: (prefs: any) => api.patch('/api/preferences', prefs),
};

// Ideas API
export const ideasAPI = {
  generate: () => api.post('/api/ideas/generate'),
  list: (skip = 0, limit = 20) =>
    api.get('/api/ideas', { params: { skip, limit } }),
  get: (id: string) => api.get(`/api/ideas/${id}`),
  delete: (id: string) => api.delete(`/api/ideas/${id}`),
};

// Reviews API
export const reviewsAPI = {
  create: (review: any) => api.post('/api/reviews', review),
  list: (skip = 0, limit = 20) =>
    api.get('/api/reviews', { params: { skip, limit } }),
  update: (id: string, review: any) =>
    api.patch(`/api/reviews/${id}`, review),
  getTopActivities: () => api.get('/api/reviews/analytics/top-activities'),
  getTrends: () => api.get('/api/reviews/analytics/trends'),
};

export default api;
