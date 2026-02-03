/**
 * 認証API
 */
import apiClient from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  company_name: string;
  industry?: string;
  plan_type: string;
  email: string;
  password: string;
  password_confirm: string;
}

export interface AuthUser {
  id: string;
  email: string;
  role: string;
  company_id: string;
}

export interface AuthResponse {
  user: AuthUser;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },
};
