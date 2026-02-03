/**
 * チャットAPI
 */
import apiClient from './client';

export interface ChatMessage {
  content: string;
}

export interface ChatResponse {
  message: string;
  sentiment_score: number;
  topics: string[];
  urgency: number;
  risk_flags: string[];
}

export interface DailyScoreResponse {
  date: string;
  sentiment_score: number;
  fatigue_level?: number;
  sleep_hours?: number;
  risk_level: string;
}

// チャット履歴関連のインターフェース
export interface ChatHistoryMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
  sentiment_score?: number;
  created_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatHistoryMessage[];
  total: number;
  limit: number;
  offset: number;
}

export interface SaveChatMessageRequest {
  role: 'user' | 'ai';
  content: string;
  sentiment_score?: number;
}

export interface SaveChatMessageResponse {
  id: string;
  success: boolean;
}

export interface DeleteChatHistoryResponse {
  deleted_count: number;
  success: boolean;
}

export const chatApi = {
  sendMessage: async (data: ChatMessage): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/api/v1/chat/message', data);
    return response.data;
  },

  getDailyScores: async (): Promise<DailyScoreResponse[]> => {
    const response = await apiClient.get<DailyScoreResponse[]>('/api/v1/chat/daily-scores');
    return response.data;
  },

  // チャット履歴API
  getHistory: async (limit: number = 50, offset: number = 0): Promise<ChatHistoryResponse> => {
    const response = await apiClient.get<ChatHistoryResponse>('/api/v1/chat/history', {
      params: { limit, offset }
    });
    return response.data;
  },

  saveMessage: async (data: SaveChatMessageRequest): Promise<SaveChatMessageResponse> => {
    const response = await apiClient.post<SaveChatMessageResponse>('/api/v1/chat/history', data);
    return response.data;
  },

  deleteHistory: async (): Promise<DeleteChatHistoryResponse> => {
    const response = await apiClient.delete<DeleteChatHistoryResponse>('/api/v1/chat/history');
    return response.data;
  },

  deleteMessage: async (messageId: string): Promise<{ success: boolean }> => {
    const response = await apiClient.delete<{ success: boolean }>(`/api/v1/chat/history/${messageId}`);
    return response.data;
  },
};
