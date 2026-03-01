import apiClient from './client';
import type {
  ConfigGenerateRequest,
  ConfigGenerateResponse,
  ConfigHistoryResponse,
  ConfigStatsResponse,
  CategoriesResponse,
  Category,
  ConfigMode,
  GlobalSetting,
} from '@/shared/types';

export const configApi = {
  /**
   * Генерация конфига (базовый метод)
   */
  async generate(request: ConfigGenerateRequest): Promise<ConfigGenerateResponse> {
    return apiClient.post<ConfigGenerateResponse>('/config/generate', request);
  },

  /**
   * Генерация конфига со всеми предметами
   */
  async generateAll(
    serverId: number,
    mode: ConfigMode,
    percentage: number
  ): Promise<ConfigGenerateResponse> {
    return apiClient.post<ConfigGenerateResponse>('/config/generate', {
      server_id: serverId,
      mode,
      percentage,
      save_to_history: true,
    });
  },

  /**
   * Генерация конфига топ-N предметов по ликвидности
   */
  async generateByLiquidity(
    serverId: number,
    mode: ConfigMode,
    percentage: number,
    topCount: number
  ): Promise<ConfigGenerateResponse> {
    return apiClient.post<ConfigGenerateResponse>('/config/generate/liquidity', null, {
      params: {
        server_id: serverId,
        mode,
        percentage,
        top_count: topCount,
      },
    });
  },

  /**
   * Генерация конфига предметов определённой категории
   */
  async generateByCategory(
    serverId: number,
    mode: ConfigMode,
    percentage: number,
    category: string
  ): Promise<ConfigGenerateResponse> {
    return apiClient.post<ConfigGenerateResponse>('/config/generate/category', null, {
      params: {
        server_id: serverId,
        mode,
        percentage,
        category,
      },
    });
  },

  /**
   * Получение статистики по конфигам
   */
  async getStats(): Promise<ConfigStatsResponse> {
    return apiClient.get<ConfigStatsResponse>('/config/stats');
  },

  /**
   * Получение истории конфигов
   */
  async getHistory(): Promise<ConfigHistoryResponse> {
    return apiClient.get<ConfigHistoryResponse>('/config/history');
  },

  /**
   * Получение категорий предметов
   */
  async getCategories(): Promise<Category[]> {
    const response = await apiClient.get<CategoriesResponse>('/config/categories');
    return response.categories;
  },

  /**
   * Получение настроек
   */
  async getSettings(): Promise<GlobalSetting[]> {
    return apiClient.get<GlobalSetting[]>('/config/settings');
  },

  /**
   * Скачивание конфига из истории (возвращает Blob с именем файла)
   */
  async download(configId: number): Promise<{ data: Blob; filename?: string }> {
    return apiClient.getBlob(`/config/history/${configId}`);
  },

  /**
   * Скачивание сгенерированного конфига в cp1251 (возвращает Blob с именем файла)
   */
  async downloadGenerated(
    serverId: number,
    mode: ConfigMode,
    percentage: number,
    saveToHistory: boolean = true
  ): Promise<{ data: Blob; filename?: string }> {
    return apiClient.postBlob('/config/generate/download', {
      server_id: serverId,
      mode,
      percentage,
      save_to_history: saveToHistory,
    });
  },

  /**
   * Скачивание конфига топ-N по ликвидности в cp1251 (возвращает Blob с именем файла)
   */
  async downloadByLiquidity(
    serverId: number,
    mode: ConfigMode,
    percentage: number,
    topCount: number,
    saveToHistory: boolean = true
  ): Promise<{ data: Blob; filename?: string }> {
    return apiClient.postBlob('/config/generate/download', {
      server_id: serverId,
      mode,
      percentage,
      top_count: topCount,
      save_to_history: saveToHistory,
    });
  },

  /**
   * Скачивание конфига по категории в cp1251 (возвращает Blob с именем файла)
   */
  async downloadByCategory(
    serverId: number,
    mode: ConfigMode,
    percentage: number,
    category: string,
    saveToHistory: boolean = true
  ): Promise<{ data: Blob; filename?: string }> {
    return apiClient.postBlob('/config/generate/download', {
      server_id: serverId,
      mode,
      percentage,
      category,
      save_to_history: saveToHistory,
    });
  },

  /**
   * Удаление конфига из истории
   */
  async deleteHistory(configId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/config/history/${configId}`);
  },
};
