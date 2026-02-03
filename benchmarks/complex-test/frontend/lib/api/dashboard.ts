/**
 * ダッシュボードAPI
 */
import apiClient from './client';

export interface DashboardStats {
  total_employees: number;
  high_stress_count: number;
  stress_check_completion_rate: number;
  average_stress_score: number;
}

export interface DepartmentStat {
  department_name: string;
  average_score: number;
  high_stress_count: number;
  employee_count: number;
}

export interface AlertItem {
  id: string;
  department_name: string;
  alert_level: string;
  message: string;
  created_at: string;
}

export interface RecommendationItem {
  id: string;
  title: string;
  description: string;
  department_name?: string;
  priority: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  department_stats: DepartmentStat[];
  alerts: AlertItem[];
  recommendations: RecommendationItem[];
}

export type PeriodFilter = 'all' | 'thisMonth' | 'lastMonth' | '3months' | '6months' | '1year';

export interface DashboardQueryParams {
  departmentId?: string;
  period?: PeriodFilter;
  startDate?: string;
  endDate?: string;
}

export const dashboardApi = {
  getCompanyDashboard: async (companyId: string, params?: DashboardQueryParams): Promise<DashboardResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.departmentId) {
      queryParams.append('department_id', params.departmentId);
    }
    if (params?.period && params.period !== 'all') {
      queryParams.append('period', params.period);
    }
    if (params?.startDate) {
      queryParams.append('start_date', params.startDate);
    }
    if (params?.endDate) {
      queryParams.append('end_date', params.endDate);
    }
    const queryString = queryParams.toString();
    const url = `/api/v1/dashboard/company/${companyId}${queryString ? `?${queryString}` : ''}`;
    const response = await apiClient.get<DashboardResponse>(url);
    return response.data;
  },

  getAlerts: async (): Promise<AlertItem[]> => {
    const response = await apiClient.get<AlertItem[]>('/api/v1/dashboard/alerts');
    return response.data;
  },
};
