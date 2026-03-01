'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings, Save } from 'lucide-react';
import { Card, CardContent, Button } from '@/shared/ui';
import { useToast } from '@/shared/ui/Toast';

interface GenerationSettingsState {
  allowAll: boolean;
  allowLiquidity: boolean;
  allowCategory: boolean;
}

export function GenerationSettings() {
  const toast = useToast();
  const [settings, setSettings] = useState<GenerationSettingsState>({
    allowAll: true,
    allowLiquidity: true,
    allowCategory: true,
  });
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // TODO: Реализовать API endpoint для сохранения настроек генерации
      // await adminApi.updateGenerationSettings(settings);
      
      // Временная заглушка
      await new Promise(resolve => setTimeout(resolve, 500));
      
      toast.success('Настройки генерации сохранены', 'Успешно');
    } catch (error) {
      toast.error('Не удалось сохранить настройки', 'Ошибка');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl"
    >
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-4 mb-6">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <Settings className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">
                Настройки генерации конфигов
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Управление доступными способами генерации
              </p>
            </div>
          </div>

          <div className="space-y-4 mb-6">
            <label className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={settings.allowAll}
                  onChange={(e) => setSettings({ ...settings, allowAll: e.target.checked })}
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
                  checked={settings.allowLiquidity}
                  onChange={(e) => setSettings({ ...settings, allowLiquidity: e.target.checked })}
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
                  checked={settings.allowCategory}
                  onChange={(e) => setSettings({ ...settings, allowCategory: e.target.checked })}
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
            onClick={handleSave}
            isLoading={isSaving}
            icon={<Save className="h-4 w-4" />}
            className="w-full"
          >
            Сохранить настройки
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}
