import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 20_000,
});

export const getSummary = async (days) => {
  const response = await api.get("/api/dashboard/summary", { params: { days } });
  return response.data;
};

export const getHierarchy = async (days) => {
  const response = await api.get("/api/hierarchy", { params: { days } });
  return response.data;
};

export const searchTickets = async (query) => {
  const response = await api.get("/api/search", { params: { q: query } });
  return response.data;
};

export const getCacheStatus = async () => {
  const response = await api.get("/api/cache/status");
  return response.data;
};

export const refreshCache = async () => {
  const response = await api.post("/api/cache/refresh");
  return response.data;
};
