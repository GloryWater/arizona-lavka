import apiClient from './client';
import type {
  AdminUser,
  AdminLog,
  AuditLog,
  GlobalSetting,
  MaintenanceStatus,
} from '@/shared/types';

export interface AdminStatsSummary {
  total_users: number;
  total_configs: number;
  dau: number;
  mau: number;
  avg_configs_per_user_per_day: number;
}

interface AdminUsersParams {
  page?: number;
  limit?: number;
  search?: string;
  sort_by?: 'id' | 'username' | 'email' | 'created_at' | 'configs_count';
}

interface AdminLogsParams {
  page?: number;
  limit?: number;
  user_id?: number;
  event_type?: string;
  search_query?: string;
  date_from?: string;
  date_to?: string;
}

interface AuditLogsParams {
  page?: number;
  limit?: number;
  user_id?: number;
  action?: string;
  status_filter?: string;
  search_query?: string;
  date_from?: string;
  date_to?: string;
}

export interface StatsChartData {
  date: string;
  registrations: number;
  configs_generated: number;
}

export interface StatsParams {
  start_date?: string;
  end_date?: string;
}

export const adminApi = {
  // ============================================================================
  // STATS
  // ============================================================================

  /**
   * Получение общей статистики
   */
  async getStats(): Promise<AdminStatsSummary> {
    return apiClient.get<AdminStatsSummary>('/v1/admin/stats/summary');
  },

  /**
   * Получение данных для графика
   */
  async getStatsChartData(params?: StatsParams): Promise<StatsChartData[]> {
    return apiClient.get<StatsChartData[]>('/v1/admin/stats/charts', {
      params,
    });
  },

  // ============================================================================
  // USERS
  // ============================================================================

  /**
   * Получение списка пользователей
   */
  async getUsers(params?: AdminUsersParams): Promise<AdminUser[]> {
    const response = await apiClient.get<AdminUser[]>('/v1/admin/users', { params });
    return Array.isArray(response) ? response : [];
  },

  /**
   * Экспорт пользователей в CSV
   */
  async exportUsers(format: 'csv' = 'csv'): Promise<Blob> {
    return apiClient.get<Blob>(`/v1/admin/users/export`, {
      params: { format },
      responseType: 'blob',
    });
  },

  /**
   * Получение пользователя по ID
   */
  async getUser(userId: number): Promise<AdminUser> {
    return apiClient.get<AdminUser>(`/v1/admin/users/${userId}`);
  },

  /**
   * Обновление пользователя
   */
  async updateUser(
    userId: number,
    data: Partial<AdminUser>
  ): Promise<AdminUser> {
    return apiClient.patch<AdminUser>(`/v1/admin/users/${userId}`, data);
  },

  /**
   * Удаление пользователя
   */
  async deleteUser(userId: number): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/v1/admin/users/${userId}`);
  },

  /**
   * Назначение роли администратора
   */
  async makeAdmin(userId: number): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>(`/v1/admin/users/${userId}/make-admin`);
  },

  /**
   * Снятие роли администратора
   */
  async removeAdmin(userId: number): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>(`/v1/admin/users/${userId}/remove-admin`);
  },

  /**
   * Блокировка пользователя
   */
  async banUser(userId: number, reason?: string): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>(`/v1/admin/users/${userId}/ban`, {
      reason,
    });
  },

  /**
   * Разблокировка пользователя
   */
  async unbanUser(userId: number): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>(`/v1/admin/users/${userId}/unban`);
  },

  // ============================================================================
  // LOGS
  // ============================================================================

  /**
   * Получение логов админ-панели
   */
  async getLogs(params?: AdminLogsParams): Promise<AdminLog[]> {
    const response = await apiClient.get<AdminLog[]>('/v1/admin/logs', { params });
    return Array.isArray(response) ? response : [];
  },

  /**
   * Получение аудиторских логов
   */
  async getAuditLogs(params?: AuditLogsParams): Promise<AuditLog[]> {
    const response = await apiClient.get<AuditLog[]>('/v1/admin/logs/audit', { params });
    return Array.isArray(response) ? response : [];
  },

  /**
   * Экспорт логов
   */
  async exportLogs(format: 'csv' | 'json'): Promise<Blob> {
    return apiClient.get<Blob>('/v1/admin/users/export', {
      params: { format },
      responseType: 'blob',
    });
  },

  // ============================================================================
  // SETTINGS
  // ============================================================================

  /**
   * Получение всех настроек
   */
  async getSettings(): Promise<GlobalSetting[]> {
    return apiClient.get<GlobalSetting[]>('/v1/admin/settings');
  },

  /**
   * Получение настройки по ключу
   */
  async getSetting(key: string): Promise<GlobalSetting> {
    return apiClient.get<GlobalSetting>(`/v1/admin/settings/${key}`);
  },

  /**
   * Обновление настройки
   */
  async updateSetting(
    key: string,
    value: Record<string, unknown>
  ): Promise<GlobalSetting> {
    return apiClient.patch<GlobalSetting>(`/v1/admin/settings/${key}`, { value });
  },

  // ============================================================================
  // MAINTENANCE
  // ============================================================================

  /**
   * Получение статуса maintenance режима
   */
  async getMaintenanceStatus(): Promise<MaintenanceStatus> {
    return apiClient.get<MaintenanceStatus>('/v1/admin/maintenance/status');
  },

  /**
   * Включение maintenance режима
   */
  async enableMaintenance(options?: { message?: string; estimated_end?: string }): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/v1/admin/maintenance/enable', {
      message: options?.message,
      estimated_end: options?.estimated_end,
    });
  },

  /**
   * Выключение maintenance режима
   */
  async disableMaintenance(): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/v1/admin/maintenance/disable');
  },
};
