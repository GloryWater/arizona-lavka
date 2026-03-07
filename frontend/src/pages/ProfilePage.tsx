'use client';

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  User,
  Mail,
  Calendar,
  Shield,
  Crown,
  LogOut,
  Save,
  Key,
  Eye,
  EyeOff,
  Lock,
  Download,
  FileText,
} from 'lucide-react';
import { useAuthStore } from '@/features/auth/model/useAuthStore';
import { useToast } from '@/shared/ui/Toast';
import { authApi, configApi } from '@/shared/api';
import {
  Card,
  CardContent,
  Button,
  Input,
  Badge,
  EmptyState,
} from '@/shared/ui';
import { formatDate } from '@/shared/lib/helpers';

export function ProfilePage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { user, logout, refreshUser } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});

  const handleSaveProfile = async () => {
    setIsLoading(true);
    try {
      await authApi.updateProfile(formData);
      await refreshUser();
      toast.success('Профиль успешно обновлен');
      setIsEditing(false);
    } catch {
      toast.error('Не удалось обновить профиль', 'Ошибка');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePassword = async () => {
    setPasswordErrors({});

    if (passwordData.new_password.length < 8) {
      setPasswordErrors({ new_password: 'Пароль должен быть не менее 8 символов' });
      return;
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordErrors({ confirm_password: 'Пароли не совпадают' });
      return;
    }

    setIsLoading(true);
    try {
      await authApi.changePassword(
        passwordData.current_password,
        passwordData.new_password
      );
      toast.success('Пароль успешно изменен');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось изменить пароль';
      toast.error(message, 'Ошибка');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleDownloadConfig = async (configId: number) => {
    try {
      const response = await configApi.download(configId);
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.filename ?? `config_${configId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Конфиг скачан', 'Успешно');
    } catch {
      toast.error('Не удалось скачать конфиг', 'Ошибка');
    }
  };

  // Загрузка истории конфигов
  const { data: configHistory } = useQuery({
    queryKey: ['user-config-history'],
    queryFn: () => configApi.getHistory(),
    staleTime: 1000 * 60 * 5,
  });

  if (!user) {
    return (
      <div className="container max-w-screen-3xl px-4 md:px-6 py-8">
        <EmptyState
          title="Требуется авторизация"
          description="Войдите в свой аккаунт для просмотра профиля"
          icon={<User className="h-16 w-16" />}
          action={
            <Button onClick={() => navigate('/login')}>
              Войти
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="container max-w-screen-3xl px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto"
      >
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
            Профиль
          </h1>
          <p className="text-muted-foreground">
            Управление настройками аккаунта
          </p>
        </div>

        <div className="space-y-6">
          {/* Profile Info */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start space-x-3 sm:space-x-4 mb-4 sm:mb-6">
                <div className="h-16 w-16 sm:h-20 sm:w-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25 flex-shrink-0">
                  <User className="h-8 w-8 sm:h-10 sm:w-10 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl sm:text-2xl font-bold text-foreground truncate">
                    {user.username}
                  </h2>
                  <div className="flex items-center gap-1 sm:gap-2 mt-1 flex-wrap">
                    <Badge variant={user.role === 'admin' ? 'destructive' : 'primary'}>
                      {user.role === 'admin' ? (
                        <>
                          <Shield className="h-3 w-3" />
                          <span className="hidden xs:inline">Администратор</span>
                          <span className="xs:hidden">Admin</span>
                        </>
                      ) : (
                        <>
                          <User className="h-3 w-3" />
                          <span className="hidden xs:inline">Пользователь</span>
                          <span className="xs:hidden">User</span>
                        </>
                      )}
                    </Badge>
                    {user.is_premium && (
                      <Badge variant="warning">
                        <Crown className="h-3 w-3" />
                        <span className="hidden xs:inline">Premium</span>
                      </Badge>
                    )}
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={handleLogout}
                  icon={<LogOut className="h-4 w-4" />}
                  className="flex-shrink-0 w-full sm:w-auto mt-2 sm:mt-0"
                >
                  Выход
                </Button>
              </div>

              {/* Info Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6">
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50">
                  <Mail className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-muted-foreground truncate">Email</p>
                    <p className="font-medium truncate">{user.email}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50">
                  <Calendar className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-muted-foreground truncate">
                      Зарегистрирован
                    </p>
                    <p className="font-medium truncate">{formatDate(user.created_at)}</p>
                  </div>
                </div>
                {user.last_active_at && (
                  <div className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50 sm:col-span-2">
                    <User className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-muted-foreground truncate">
                        Последняя активность
                      </p>
                      <p className="font-medium truncate">{formatDate(user.last_active_at)}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Edit Name */}
              <div className="border-t border-border pt-6">
                <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                  <h3 className="font-semibold text-foreground">
                    Личная информация
                  </h3>
                  {!isEditing && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(true)}
                      className="w-full sm:w-auto"
                    >
                      Редактировать
                    </Button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <Input
                    label="Имя"
                    value={formData.first_name}
                    onChange={(e) =>
                      setFormData({ ...formData, first_name: e.target.value })
                    }
                    disabled={!isEditing}
                    icon={<User className="h-5 w-5" />}
                  />
                  <Input
                    label="Фамилия"
                    value={formData.last_name}
                    onChange={(e) =>
                      setFormData({ ...formData, last_name: e.target.value })
                    }
                    disabled={!isEditing}
                    icon={<User className="h-5 w-5" />}
                  />
                </div>

                {isEditing && (
                  <div className="flex justify-end gap-2 mt-4 flex-wrap">
                    <Button
                      variant="ghost"
                      onClick={() => setIsEditing(false)}
                      className="w-full sm:w-auto"
                    >
                      Отмена
                    </Button>
                    <Button
                      onClick={handleSaveProfile}
                      isLoading={isLoading}
                      icon={<Save className="h-4 w-4" />}
                      className="w-full sm:w-auto"
                    >
                      Сохранить
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Change Password */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Key className="h-5 w-5 text-muted-foreground" />
                <h3 className="font-semibold text-foreground">
                  Смена пароля
                </h3>
              </div>

              <div className="space-y-4">
                <Input
                  label="Текущий пароль"
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={passwordData.current_password}
                  onChange={(e) =>
                    setPasswordData({
                      ...passwordData,
                      current_password: e.target.value,
                    })
                  }
                  icon={<Lock className="h-5 w-5" />}
                >
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showCurrentPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </Input>

                <Input
                  label="Новый пароль"
                  type={showNewPassword ? 'text' : 'password'}
                  value={passwordData.new_password}
                  onChange={(e) =>
                    setPasswordData({
                      ...passwordData,
                      new_password: e.target.value,
                    })
                  }
                  error={passwordErrors.new_password}
                  icon={<Lock className="h-5 w-5" />}
                >
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showNewPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </Input>

                <Input
                  label="Подтверждение нового пароля"
                  type={showNewPassword ? 'text' : 'password'}
                  value={passwordData.confirm_password}
                  onChange={(e) =>
                    setPasswordData({
                      ...passwordData,
                      confirm_password: e.target.value,
                    })
                  }
                  error={passwordErrors.confirm_password}
                  icon={<Lock className="h-5 w-5" />}
                />

                <Button
                  onClick={handleChangePassword}
                  isLoading={isLoading}
                  icon={<Key className="h-4 w-4" />}
                >
                  Изменить пароль
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Config History */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <h3 className="font-semibold text-foreground">
                  История конфигов
                </h3>
              </div>

              {!configHistory || configHistory.length === 0 ? (
                <EmptyState
                  title="Нет конфигов"
                  description="Вы ещё не сгенерировали ни одного конфига"
                  icon={<FileText className="h-16 w-16" />}
                />
              ) : (
                <div className="space-y-3">
                  {configHistory.slice(0, 10).map((config) => (
                    <div
                      key={config.id}
                      className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                          <FileText className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-foreground">
                              {config.server_name}
                            </p>
                            <Badge variant={config.mode === 'SELL' ? 'success' : 'primary'}>
                              {config.mode === 'SELL' ? 'Продажа' : 'Скупка'}
                            </Badge>
                            <Badge variant="neutral">
                              {config.items_count} предметов
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {new Date(config.created_at).toLocaleString('ru-RU')}
                            {config.percentage !== 0 && (
                              <span className="ml-2">
                                ({config.percentage > 0 ? '+' : ''}{config.percentage}%)
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadConfig(config.id)}
                        icon={<Download className="h-4 w-4" />}
                      >
                        Скачать
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </div>
  );
}
