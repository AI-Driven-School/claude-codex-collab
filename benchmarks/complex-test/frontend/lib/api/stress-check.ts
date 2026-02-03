/**
 * ストレスチェックAPI
 */
import apiClient from './client';

export interface StressCheckQuestion {
  id: string;
  text: string;
  category: string;
}

export interface StressCheckAnswer {
  answers: Record<string, number>;
}

export interface StressCheckResult {
  id: string;
  period: string;
  total_score: number;
  is_high_stress: boolean;
  job_stress_score: number;
  stress_reaction_score: number;
  support_score: number;
  satisfaction_score: number;
}

export interface StressCheckHistoryItem {
  id: string;
  period: string;
  total_score: number;
  is_high_stress: boolean;
}

export interface DraftAnswerResponse {
  answers: Record<string, number>;
  updated_at?: string;
}

export const stressCheckApi = {
  getQuestions: async (): Promise<{ questions: StressCheckQuestion[]; already_taken?: boolean; message?: string }> => {
    const response = await apiClient.get<{ questions: StressCheckQuestion[]; already_taken?: boolean; message?: string }>('/api/v1/stress-check/questions');
    return response.data;
  },

  submit: async (data: StressCheckAnswer): Promise<StressCheckResult> => {
    const response = await apiClient.post<StressCheckResult>('/api/v1/stress-check/submit', data);
    return response.data;
  },

  getHistory: async (): Promise<StressCheckHistoryItem[]> => {
    const response = await apiClient.get<StressCheckHistoryItem[]>('/api/v1/stress-check/history');
    return response.data;
  },

  getResult: async (checkId: string): Promise<StressCheckResult> => {
    const response = await apiClient.get<StressCheckResult>(`/api/v1/stress-check/result/${checkId}`);
    return response.data;
  },

  getDraft: async (): Promise<DraftAnswerResponse> => {
    const response = await apiClient.get<DraftAnswerResponse>('/api/v1/stress-check/draft');
    return response.data;
  },

  saveDraft: async (answers: Record<string, number>): Promise<DraftAnswerResponse> => {
    const response = await apiClient.post<DraftAnswerResponse>('/api/v1/stress-check/draft', { answers });
    return response.data;
  },

  deleteDraft: async (): Promise<void> => {
    await apiClient.delete('/api/v1/stress-check/draft');
  },

  migrateDraft: async (answers: Record<string, number>): Promise<DraftAnswerResponse> => {
    const response = await apiClient.post<DraftAnswerResponse>('/api/v1/stress-check/draft/migrate', { answers });
    return response.data;
  },
};
