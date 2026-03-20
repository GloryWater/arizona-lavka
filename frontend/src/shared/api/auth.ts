import apiClient from './client';
import type {
  User,
  UserProfile,
  TokenResponse,
  RegisterData,
  LoginData,
  TelegramLoginData,
} from '@/shared/types';

export const authApi = {
  /**
   * Регистрация пользователя
   */
  async register(data: RegisterData): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/register', data);
  },

  /**
   * Вход пользователя
   */
  async login(data: LoginData): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/login', data);
  },

  /**
   * Вход через Telegram
   */
  async telegramLogin(data: TelegramLoginData): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/telegram/login', data);
  },

  /**
   * Обновление токена
   */
  async refresh(refreshToken: string): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken });
  },

  /**
   * Выход пользователя
   */
  async logout(): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/logout');
  },

  /**
   * Получение информации о текущем пользователе
   */
  async getMe(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * Обновление профиля
   */
  async updateProfile(data: Partial<UserProfile>): Promise<User> {
    return apiClient.patch<User>('/auth/me', data);
  },

  /**
   * Смена пароля
   */
  async changePassword(
    oldPassword: string,
    newPassword: string
  ): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  /**
   * Подтверждение email токеном (POST версия для frontend)
   */
  async verifyEmailByToken(data: { token: string }): Promise<{ message: string; is_email_verified: boolean }> {
    return apiClient.post('/auth/verify-email-token', data);
  },
};
