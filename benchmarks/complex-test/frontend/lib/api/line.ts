import apiClient from './client';

export interface LineStatus {
  is_linked: boolean;
  link_code: string | null;
}

export interface LineLinkCode {
  link_code: string;
  instruction: string;
}

export const lineApi = {
  /**
   * LINE連携状態を取得
   */
  getStatus: async (): Promise<LineStatus> => {
    const response = await apiClient.get('/api/v1/user/line/status');
    return response.data;
  },

  /**
   * LINE連携コードを生成
   */
  generateLinkCode: async (): Promise<LineLinkCode> => {
    const response = await apiClient.post('/api/v1/user/line/generate-code');
    return response.data;
  },

  /**
   * LINE連携を解除
   */
  unlink: async (): Promise<void> => {
    await apiClient.delete('/api/v1/user/line/unlink');
  },
};
