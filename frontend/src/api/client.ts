// Scaffold-owned API client. Domain calls are added by generated modules importing `api`.
import axios from "axios";
import { API_BASE } from "../config";

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface Token { access_token: string; token_type?: string }
export interface CurrentUser { id: string; email: string; created_at: string }

export const register = (email: string, password: string) =>
  api.post<Token>("/api/auth/register", { email, password });
export const login = (email: string, password: string) =>
  api.post<Token>("/api/auth/login", { email, password });
export const getMe = () => api.get<CurrentUser>("/api/auth/me");
