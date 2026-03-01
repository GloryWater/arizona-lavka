'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings,
  Save,
  AlertTriangle,
  CheckCircle,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { adminApi } from '@/shared/api/admin';
import { useToast } from '@/shared/ui/Toast';
import type { GlobalSetting } from '@/shared/types';
import {
  Card,
  CardContent,
  Button,
  Input,
  Alert,
  Badge,
  Skeleton,
} from '@/shared/ui';

export function AdminSettingsPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [maintenanceMessage, setMaintenanceMessage] = useState('');
  const [maintenanceEnd, setMaintenanceEnd] = useState('');
  
  // Настройки генерации конфигов
  const [configGenerationSettings, setConfigGenerationSettings] = useState({
    allow_all: true,
    allow_liquidity: true,
    allow_category: true,
  });

  // Загрузка настроек
  const { data: settings, isLoading } = useQuery({
    queryKey: ['admin-settings'],
    queryFn: () => adminApi.getSettings(),
    staleTime: 1000 * 60 * 5,
  });

  // Загрузка статуса maintenance
  const { data: maintenanceStatus } = useQuery({
    queryKey: ['maintenance-status'],
    queryFn: () => adminApi.getMaintenanceStatus(),
    staleTime: 1000 * 30,
  });

  // Загрузка настроек генерации конфигов
  useEffect(() => {
    const configSetting = settings?.find(s => s.key === 'config_generation_methods');
    if (configSetting && typeof configSetting.value === 'object' && configSetting.value !== null) {
      const value = configSetting.value as Record<string, boolean>;
      setConfigGenerationSettings({
        allow_all: value.allow_all ?? true,
        allow_liquidity: value.allow_liquidity ?? true,
        allow_category: value.allow_category ?? true,
      });
    }
  }, [settings]);

  // Мутация обновления настройки генерации
  const updateConfigGenerationMutation = useMutation({
    mutationFn: async (value: typeof configGenerationSettings) => {
      return adminApi.updateSetting('config_generation_methods', value as Record<string, unknown>);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-settings'] });
      toast.success('Настройки генерации сохранены', 'Успешно');
    },
    onError: () => {
      toast.error('Не удалось сохранить настройки', 'Ошибка');
    },
  });

  // Мутация обновления настройки
  const updateSettingMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: Record<string, unknown> }) => {
      return adminApi.updateSetting(key, value);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-settings'] });
      toast.success('Настройка сохранена', 'Успешно');
    },
    onError: () => {
      toast.error('Не удалось сохранить настройку', 'Ошибка');
    },
  });

  // Мутация включения maintenance
  const enableMaintenanceMutation = useMutation({
    mutationFn: async () => {
      return adminApi.enableMaintenance({
        message: maintenanceMessage || 'Технические работы',
        estimated_end: maintenanceEnd || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-status'] });
      toast.success('Режим обслуживания включён', 'Успешно');
    },
    onError: () => {
      toast.error('Не удалось включить режим обслуживания', 'Ошибка');
    },
  });

  // Мутация выключения maintenance
  const disableMaintenanceMutation = useMutation({
    mutationFn: async () => {
      return adminApi.disableMaintenance();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-status'] });
      toast.success('Режим обслуживания выключен', 'Успешно');
    },
    onError: () => {
      toast.error('Не удалось выключить режим обслуживания', 'Ошибка');
    },
  });

  const isMaintenanceEnabled = maintenanceStatus?.enabled === true;

  return (
    <div className="container max-w-screen-2xl px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center space-x-4">
          <div className="h-12 w-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-orange-500/25">
            <Settings className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">Настройки системы</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Глобальные настройки и режим обслуживания
            </p>
          </div>
        </div>
      </motion.div>

      {/* Config Generation Settings */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
              <Settings className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Способы генерации конфигов
              </h2>
              <p className="text-sm text-muted-foreground">
                Включите или отключите доступные методы генерации
              </p>
            </div>
          </div>

          <div className="space-y-4 mb-6">
            <label className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={configGenerationSettings.allow_all}
                  onChange={(e) => setConfigGenerationSettings(prev => ({
                    ...prev,
                    allow_all: e.target.checked,
                  }))}
                  className="h-4 w-4 text-primary rounded focus:ring-primary"
                />
                <div>
                  <p className="font-medium text-foreground">Все предметы</p>
                  <p className="text-sm text-muted-foreground">
                    Генерация конфига со всеми предметами на сервере
                  </p>
                </div>
              </div>
            </label>

            <label className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={configGenerationSettings.allow_liquidity}
                  onChange={(e) => setConfigGenerationSettings(prev => ({
                    ...prev,
                    allow_liquidity: e.target.checked,
                  }))}
                  className="h-4 w-4 text-primary rounded focus:ring-primary"
                />
                <div>
                  <p className="font-medium text-foreground">По ликвидности</p>
                  <p className="text-sm text-muted-foreground">
                    Генерация топ-N предметов по ликвидности
                  </p>
                </div>
              </div>
            </label>

            <label className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={configGenerationSettings.allow_category}
                  onChange={(e) => setConfigGenerationSettings(prev => ({
                    ...prev,
                    allow_category: e.target.checked,
                  }))}
                  className="h-4 w-4 text-primary rounded focus:ring-primary"
                />
                <div>
                  <p className="font-medium text-foreground">По категориям</p>
                  <p className="text-sm text-muted-foreground">
                    Генерация предметов определённой категории
                  </p>
                </div>
              </div>
            </label>
          </div>

          <Button
            onClick={() => updateConfigGenerationMutation.mutate(configGenerationSettings)}
            isLoading={updateConfigGenerationMutation.isPending}
            icon={<Save className="h-4 w-4" />}
            className="w-full"
          >
            Сохранить настройки генерации
          </Button>
        </CardContent>
      </Card>

      {/* Maintenance Mode */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${isMaintenanceEnabled ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                {isMaintenanceEnabled ? (
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                ) : (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  Режим обслуживания
                </h2>
                <p className="text-sm text-muted-foreground">
                  {isMaintenanceEnabled ? 'Включён' : 'Выключен'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isMaintenanceEnabled ? (
                <Badge variant="destructive">Активен</Badge>
              ) : (
                <Badge variant="success">Не активен</Badge>
              )}
            </div>
          </div>

          {isMaintenanceEnabled && maintenanceStatus?.info && (
            <Alert
              variant="warning"
              title="Информация"
              description={maintenanceStatus.info.message || 'Технические работы'}
              className="mb-4"
            />
          )}

          {!isMaintenanceEnabled ? (
            <div className="space-y-4">
              <Input
                label="Сообщение для пользователей"
                placeholder="Технические работы. Скоро вернёмся!"
                value={maintenanceMessage}
                onChange={(e) => setMaintenanceMessage(e.target.value)}
              />
              <Input
                label="Предполагаемое время окончания (ISO 8601)"
                placeholder="2026-02-28T20:00:00Z"
                value={maintenanceEnd}
                onChange={(e) => setMaintenanceEnd(e.target.value)}
                type="datetime-local"
              />
              <Button
                variant="destructive"
                onClick={() => enableMaintenanceMutation.mutate()}
                isLoading={enableMaintenanceMutation.isPending}
                icon={<ToggleRight className="h-4 w-4" />}
              >
                Включить режим обслуживания
              </Button>
            </div>
          ) : (
            <Button
              variant="success"
              onClick={() => disableMaintenanceMutation.mutate()}
              isLoading={disableMaintenanceMutation.isPending}
              icon={<ToggleLeft className="h-4 w-4" />}
            >
              Выключить режим обслуживания
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Global Settings */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">
            Глобальные настройки
          </h2>

          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : !settings || settings.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              Настройки не найдены
            </p>
          ) : (
            <div className="space-y-4">
              {settings.map((setting) => (
                <SettingRow
                  key={setting.key}
                  setting={setting}
                  onUpdate={(key, value) => updateSettingMutation.mutate({ key, value })}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

interface SettingRowProps {
  setting: GlobalSetting;
  onUpdate: (key: string, value: Record<string, unknown>) => void;
}

function SettingRow({ setting, onUpdate }: SettingRowProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(JSON.stringify(setting.value, null, 2));

  const handleSave = () => {
    try {
      const parsedValue = JSON.parse(value);
      onUpdate(setting.key, parsedValue);
      setEditing(false);
    } catch (error) {
      console.error('Invalid JSON:', error);
    }
  };

  return (
    <div className="p-4 rounded-lg border border-border">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-foreground">{setting.key}</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            Обновлено: {new Date(setting.updated_at).toLocaleString('ru-RU')}
          </span>
          {editing ? (
            <>
              <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
                Отмена
              </Button>
              <Button variant="primary" size="sm" onClick={handleSave} icon={<Save className="h-4 w-4" />}>
                Сохранить
              </Button>
            </>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
              Редактировать
            </Button>
          )}
        </div>
      </div>
      {editing ? (
        <textarea
          className="w-full h-32 p-3 text-sm font-mono bg-muted rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-ring"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      ) : (
        <pre className="text-sm bg-muted p-3 rounded-lg overflow-auto max-h-48">
          {JSON.stringify(setting.value, null, 2)}
        </pre>
      )}
    </div>
  );
}
