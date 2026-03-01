import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import type { ApiError } from '@/shared/types';

// ============================================================================
// TYPES
// ============================================================================

interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// ============================================================================
// API CLIENT
// ============================================================================

class ApiClient {
  private instance: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_URL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.instance.interceptors.request.use(this.handleRequest.bind(this));
    this.instance.interceptors.response.use(
      this.handleResponse.bind(this),
      this.handleError.bind(this)
    );
  }

  private handleRequest(
    config: CustomAxiosRequestConfig
  ): CustomAxiosRequestConfig {
    const token = this.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }

  private handleResponse(response: AxiosResponse): AxiosResponse {
    return response;
  }

  private async handleError(
    error: AxiosError<ApiError>
  ): Promise<never> {
    const originalRequest = error.config as CustomAxiosRequestConfig;

    // Обработка 503 Maintenance Mode
    if (error.response?.status === 503 && error.response?.data?.code === 'MAINTENANCE_MODE') {
      // Перенаправляем на страницу maintenance
      window.location.href = '/maintenance';
      return Promise.reject(error);
    }

    // Если ошибка 401 и запрос ещё не был повторён
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== '/auth/refresh'
    ) {
      if (this.refreshPromise) {
        // Если уже идёт процесс обновления токена, ждём его
        try {
          const newToken = await this.refreshPromise;
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return this.instance(originalRequest);
        } catch {
          return Promise.reject(error);
        }
      }

      originalRequest._retry = true;

      this.refreshPromise = this.refreshToken();

      try {
        const newToken = await this.refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return this.instance(originalRequest);
      } catch (refreshError) {
        // Если не удалось обновить токен — выходим
        this.logout();
        return Promise.reject(refreshError);
      } finally {
        this.refreshPromise = null;
      }
    }

    return Promise.reject(error);
  }

  private async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token');
    }

    const response = await axios.post<{ access_token: string; refresh_token: string }>(
      `${this.instance.defaults.baseURL}/auth/refresh`,
      { refresh_token: refreshToken }
    );

    const { access_token, refresh_token } = response.data;
    this.setTokens(access_token, refresh_token);

    return access_token;
  }

  private getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }

  // ============================================================================
  // PUBLIC METHODS
  // ============================================================================

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  async getBlob(url: string, config?: AxiosRequestConfig): Promise<{ data: Blob; filename?: string }> {
    const response = await this.instance.get(url, {
      ...config,
      responseType: 'blob',
    });
    const filename = this.extractFilenameFromHeader(response.headers['content-disposition']);
    return { data: response.data as Blob, filename };
  }

  async postBlob(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<{ data: Blob; filename?: string }> {
    const response = await this.instance.post(url, data, {
      ...config,
      responseType: 'blob',
    });
    const filename = this.extractFilenameFromHeader(response.headers['content-disposition']);
    return { data: response.data as Blob, filename };
  }

  private extractFilenameFromHeader(contentDisposition?: string): string | undefined {
    if (!contentDisposition) return undefined;
    const match = contentDisposition.match(/filename="?([^"]+)"?/i);
    return match ? match[1] : undefined;
  }

  setToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export const apiClient = new ApiClient();
export default apiClient;
