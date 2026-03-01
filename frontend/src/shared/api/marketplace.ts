import apiClient from './client';
import type {
  OffersResponse,
  SearchResults,
  LavkaDetail,
  LavkasResponse,
  Server,
  ServersResponse,
} from '@/shared/types';

interface SearchParams {
  search_term: string;
  server_id?: number;
  limit?: number;
  offset?: number;
  sort_order?: 'asc' | 'desc' | 'none';
}

export const marketplaceApi = {
  /**
   * Поиск предложений
   */
  async search(params: SearchParams): Promise<SearchResults> {
    return apiClient.get<SearchResults>('/marketplace/search', { params });
  },

  /**
   * Получение всех предложений
   */
  async getOffers(params?: { search_term?: string; server_id?: number; sort_order?: string }): Promise<OffersResponse> {
    return apiClient.get<OffersResponse>('/marketplace/offers', { params });
  },

  /**
   * Получение списка лавок сервера
   */
  async getLavkas(serverId: number): Promise<LavkasResponse> {
    return apiClient.get<LavkasResponse>('/marketplace/lavkas', { params: { server_id: serverId } });
  },

  /**
   * Получение информации о лавке
   */
  async getLavkaDetail(lavkaUid: string, serverId?: number): Promise<LavkaDetail> {
    return apiClient.get<LavkaDetail>(
      `/marketplace/lavkas/${lavkaUid}`,
      { params: serverId ? { server_id: serverId } : undefined }
    );
  },

  /**
   * Получение списка серверов
   */
  async getServers(): Promise<Server[]> {
    const response = await apiClient.get<ServersResponse>('/marketplace/servers');
    return response.servers;
  },

  /**
   * Получение mapping предметов
   */
  async getItems(): Promise<Record<string, string>> {
    return apiClient.get<Record<string, string>>('/marketplace/items');
  },
};
