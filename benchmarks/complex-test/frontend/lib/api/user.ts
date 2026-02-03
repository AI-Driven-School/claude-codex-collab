/**
 * ユーザーAPI
 */
import apiClient from './client';

export interface UserResponse {
  id: string;
  email: string;
  role: string;
  company_id: string;
  company_name?: string | null;
}

export const userApi = {
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>('/api/v1/auth/me');
    return response.data;
  },
};
