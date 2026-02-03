/**
 * 部署管理API
 */
import apiClient from './client';

export interface Department {
  id: string;
  name: string;
  description: string | null;
  company_id: string;
  employee_count: number;
  created_at: string;
}

export interface DepartmentListResponse {
  departments: Department[];
  total: number;
}

export interface DepartmentCreate {
  name: string;
  description?: string;
}

export interface DepartmentUpdate {
  name?: string;
  description?: string;
}

export const departmentApi = {
  /**
   * 部署一覧を取得
   */
  getDepartments: async (): Promise<DepartmentListResponse> => {
    const response = await apiClient.get<DepartmentListResponse>('/api/v1/departments');
    return response.data;
  },

  /**
   * 部署詳細を取得
   */
  getDepartment: async (departmentId: string): Promise<Department> => {
    const response = await apiClient.get<Department>(`/api/v1/departments/${departmentId}`);
    return response.data;
  },

  /**
   * 部署を作成
   */
  createDepartment: async (data: DepartmentCreate): Promise<Department> => {
    const response = await apiClient.post<Department>('/api/v1/departments', data);
    return response.data;
  },

  /**
   * 部署を更新
   */
  updateDepartment: async (departmentId: string, data: DepartmentUpdate): Promise<Department> => {
    const response = await apiClient.put<Department>(`/api/v1/departments/${departmentId}`, data);
    return response.data;
  },

  /**
   * 部署を削除
   */
  deleteDepartment: async (departmentId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/departments/${departmentId}`);
  },
};
