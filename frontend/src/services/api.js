/**
 * API service — centralized Axios instance and all API call functions.
 */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Brands ─────────────────────────────────────────────────
export const getBrands = (page = 1, perPage = 20) =>
  api.get('/api/brands', { params: { page, per_page: perPage } });

export const getBrand = (id) =>
  api.get(`/api/brands/${id}`);

export const createBrand = (data) =>
  api.post('/api/brands', data);

// ── Sales ──────────────────────────────────────────────────
export const getSales = (params) =>
  api.get('/api/sales', { params });

// ── Analytics ──────────────────────────────────────────────
export const getAnalyticsSummary = () =>
  api.get('/api/analytics/summary');

export const getTrends = (brandId, period = 'monthly') =>
  api.get('/api/analytics/trends', { params: { brand_id: brandId, period } });

export const getTopBrands = (limit = 5) =>
  api.get('/api/analytics/top-brands', { params: { limit } });

export const getPlatformSplit = () =>
  api.get('/api/analytics/platform-split');

// ── ETL ────────────────────────────────────────────────────
export const triggerETL = () =>
  api.post('/api/etl/trigger');

export const getETLLogs = () =>
  api.get('/api/etl/logs');

// -- Export --
export const exportCSV = (params) =>
  api.get('/api/analytics/export', { params, responseType: 'blob' });

// -- Chat --
export const getChatRooms = () =>
  api.get('/api/chat/rooms');

export const getChatMessages = (roomId, limit = 50, beforeId) =>
  api.get(`/api/chat/rooms/${roomId}/messages`, { params: { limit, before_id: beforeId } });

export const createChatRoom = (data) =>
  api.post('/api/chat/rooms', data);

export default api;
