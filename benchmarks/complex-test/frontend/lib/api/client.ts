/**
 * APIクライアント
 */
import axios, { AxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

type RetryConfig = AxiosRequestConfig & {
  _retry?: boolean;
  _skipAuthRefresh?: boolean;
};

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

// レスポンスインターセプター: エラーハンドリング
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = (error.config || {}) as RetryConfig;
    const shouldRefresh = error.response?.status === 401 && !originalRequest._retry && !originalRequest._skipAuthRefresh;

    if (shouldRefresh) {
      originalRequest._retry = true;
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = apiClient
          .post('/api/v1/auth/refresh', null, { _skipAuthRefresh: true } as RetryConfig)
          .then(() => {})
          .finally(() => {
            isRefreshing = false;
          });
      }

      try {
        await refreshPromise;
        return apiClient(originalRequest);
      } catch {
        if (typeof window !== 'undefined') {
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }
      }
    }

    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
