import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/marketplace';
import { UserProfile, ConfigHistoryItem } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { ErrorState } from '../components/states/ErrorState';
import { User, Mail, Calendar, FileText, Download, TrendingUp } from 'lucide-react';
import { formatDate } from '../utils/constants';

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [configs, setConfigs] = useState<ConfigHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProfile = async () => {
      if (!user) {
        navigate('/login');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const [profileResponse, configsResponse] = await Promise.all([
          apiClient.get<UserProfile>('/user/profile'),
          apiClient.get<ConfigHistoryItem[]>('/config/history?limit=10'),
        ]);

        setProfile(profileResponse.data);
        setConfigs(configsResponse.data);
        // Не вызываем refreshUser() здесь, чтобы избежать бесконечного цикла
        // Данные пользователя уже актуальны из /user/profile
      } catch (err) {
        setError('Ошибка загрузки профиля');
        console.error('Error loading profile:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, navigate]); // Убрали refreshUser из зависимостей

  const handleDownloadConfig = async (configId: number, mode: string, serverId: number) => {
    try {
      const response = await apiClient.get(`/config/history/${configId}`, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `config_${mode.toLowerCase()}_${serverId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading config:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error || !profile) {
    return <ErrorState title="Ошибка" description={error || 'Профиль не найден'} />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-white mb-8">Профиль</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Информация о пользователе */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Информация</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="h-16 w-16 bg-primary-600 rounded-full flex items-center justify-center">
                  <User className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{profile.username}</h2>
                  {profile.is_premium && (
                    <span className="text-xs bg-yellow-600 text-white px-2 py-1 rounded">
                      Premium
                    </span>
                  )}
                </div>
              </div>

              <div className="border-t border-dark-border pt-4 space-y-3">
                <div className="flex items-center space-x-3 text-gray-400">
                  <Mail className="h-5 w-5" />
                  <span className="text-white">{profile.email}</span>
                </div>

                <div className="flex items-center space-x-3 text-gray-400">
                  <Calendar className="h-5 w-5" />
                  <span className="text-white">
                    {formatDate(profile.created_at)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Статистика */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Статистика</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-primary-500" />
                    <span className="text-gray-400">Конфигов создано</span>
                  </div>
                  <span className="text-xl font-bold text-white">
                    {profile.configs_count}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* История конфигов */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>История конфигов</CardTitle>
                <span className="text-sm text-gray-400">
                  Последние {configs.length} конфигов
                </span>
              </div>
            </CardHeader>
            <CardContent>
              {configs.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>У вас пока нет созданных конфигов</p>
                  <button
                    onClick={() => navigate('/config-generator')}
                    className="mt-4 text-primary-500 hover:text-primary-400"
                  >
                    Создать первый конфиг →
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {configs.map((config) => (
                    <div
                      key={config.id}
                      className="flex items-center justify-between p-4 bg-dark-border rounded-lg"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="h-10 w-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
                          <TrendingUp className="h-5 w-5 text-primary-500" />
                        </div>
                        <div>
                          <h3 className="text-white font-medium">
                            {config.server_name}
                          </h3>
                          <p className="text-sm text-gray-400">
                            {config.mode === 'SELL' ? 'Продажа' : 'Покупка'} •{' '}
                            {config.items_count} предметов •{' '}
                            {config.percentage >= 0 ? '+' : ''}{config.percentage}%
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDownloadConfig(config.id, config.mode, config.server_id)}
                        className="p-2 text-gray-400 hover:text-white transition-colors"
                        title="Скачать"
                      >
                        <Download className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
