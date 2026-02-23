import React, { useState, FormEvent, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/marketplace';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Select } from '../components/ui/Select';
import { ErrorState } from '../components/states/ErrorState';
import { Settings, Download, AlertCircle, TrendingUp, Tag, Zap } from 'lucide-react';
import { SERVERS, MODE_OPTIONS } from '../utils/constants';
import { useNavigate } from 'react-router-dom';

interface Category {
  key: string;
  name: string;
}

type GeneratorMode = 'standard' | 'liquidity' | 'category';

export function ConfigGeneratorPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatorMode, setGeneratorMode] = useState<GeneratorMode>('standard');
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    server_id: '0',
    mode: 'SELL' as 'SELL' | 'BUY',
    percentage: '-5',
    top_count: '10',
    category: 'all',
  });

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await apiClient.get<{ categories: Category[] }>('/config/categories');
        setCategories(response.data.categories);
      } catch (err) {
        console.error('Error loading categories:', err);
      }
    };
    loadCategories();
  }, []);

  const handleDownload = async (blob: Blob, filename: string) => {
    // blob содержит JSON данные в кодировке cp1251 от сервера
    // Для скачивания просто передаём blob напрямую
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      let response;
      let filename = '';
      
      // Получаем название сервера
      const selectedServer = SERVERS.find(s => s.id.toString() === formData.server_id);
      const serverName = selectedServer?.name.toLowerCase().replace(/\s+/g, '_') || 'server';
      const action = formData.mode.toLowerCase();
      // Генерируем случайное число от 4 до 7 цифр (1000-9999999)
      const randomNum = Math.floor(1000 + Math.random() * 8999999);

      if (generatorMode === 'standard') {
        response = await apiClient.post(
          '/config/generate/download',
          {
            server_id: parseInt(formData.server_id),
            mode: formData.mode,
            percentage: parseFloat(formData.percentage),
            save_to_history: true,
          },
          { responseType: 'blob' }
        );
        // Формат: action_server_numbers.json
        filename = `${action}_${serverName}_${randomNum}.json`;
      } else if (generatorMode === 'liquidity') {
        response = await apiClient.post(
          `/config/generate/liquidity?server_id=${formData.server_id}&mode=${formData.mode}&percentage=${formData.percentage}&top_count=${formData.top_count}`,
          {},
          { responseType: 'blob' }
        );
        filename = `${action}_${serverName}_${randomNum}.json`;
      } else {
        response = await apiClient.post(
          `/config/generate/category?server_id=${formData.server_id}&mode=${formData.mode}&percentage=${formData.percentage}&category=${formData.category}`,
          {},
          { responseType: 'blob' }
        );
        filename = `${action}_${serverName}_${randomNum}.json`;
      }

      handleDownload(response.data, filename);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const errorData = (err as { response?: { data?: { detail?: string } } }).response?.data;
        setError(errorData?.detail || 'Ошибка генерации конфига');
      } else {
        setError('Ошибка генерации конфига');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <Card>
          <CardContent>
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Требуется авторизация</h2>
              <p className="text-gray-400 mb-4">
                Для использования генератора конфигов необходимо войти в аккаунт
              </p>
              <Button onClick={() => navigate('/login')}>
                Войти
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Генератор конфигов</h1>
        <p className="text-gray-400">
          Создайте торговый конфиг с использованием различных стратегий
        </p>
      </div>

      {error && (
        <ErrorState title="Ошибка" description={error} onRetry={() => setError(null)} />
      )}

      {/* Выбор режима генерации */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card
          hoverable
          onClick={() => setGeneratorMode('standard')}
          className={`cursor-pointer transition-all ${
            generatorMode === 'standard' ? 'ring-2 ring-primary-500' : ''
          }`}
        >
          <CardContent className="flex flex-col items-center text-center p-6">
            <Settings className={`h-8 w-8 mb-3 ${
              generatorMode === 'standard' ? 'text-primary-500' : 'text-gray-400'
            }`} />
            <h3 className="text-white font-semibold mb-1">Стандартный</h3>
            <p className="text-sm text-gray-400">
              Все предметы с IQR анализом
            </p>
          </CardContent>
        </Card>

        <Card
          hoverable
          onClick={() => setGeneratorMode('liquidity')}
          className={`cursor-pointer transition-all ${
            generatorMode === 'liquidity' ? 'ring-2 ring-green-500' : ''
          }`}
        >
          <CardContent className="flex flex-col items-center text-center p-6">
            <TrendingUp className={`h-8 w-8 mb-3 ${
              generatorMode === 'liquidity' ? 'text-green-500' : 'text-gray-400'
            }`} />
            <h3 className="text-white font-semibold mb-1">По ликвидности</h3>
            <p className="text-sm text-gray-400">
              Топ-N самых ликвидных предметов
            </p>
          </CardContent>
        </Card>

        <Card
          hoverable
          onClick={() => setGeneratorMode('category')}
          className={`cursor-pointer transition-all ${
            generatorMode === 'category' ? 'ring-2 ring-blue-500' : ''
          }`}
        >
          <CardContent className="flex flex-col items-center text-center p-6">
            <Tag className={`h-8 w-8 mb-3 ${
              generatorMode === 'category' ? 'text-blue-500' : 'text-gray-400'
            }`} />
            <h3 className="text-white font-semibold mb-1">По категории</h3>
            <p className="text-sm text-gray-400">
              Предметы определённой категории
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Settings className="h-6 w-6 text-primary-500" />
            <CardTitle>Параметры генерации</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Сервер и режим */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Сервер"
                options={SERVERS.map(s => ({ value: String(s.id), label: s.name }))}
                value={formData.server_id}
                onChange={(e) => setFormData({ ...formData, server_id: e.target.value })}
              />

              <Select
                label="Режим"
                options={MODE_OPTIONS}
                value={formData.mode}
                onChange={(e) => setFormData({ ...formData, mode: e.target.value as 'SELL' | 'BUY' })}
              />
            </div>

            {/* Процент */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Процентная корректировка цены (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="-50"
                max="50"
                className="input w-full"
                value={formData.percentage}
                onChange={(e) => setFormData({ ...formData, percentage: e.target.value })}
              />
              <p className="mt-1 text-sm text-gray-400">
                Отрицательное значение уменьшит цену, положительное — увеличит
              </p>
            </div>

            {/* Дополнительные параметры в зависимости от режима */}
            {generatorMode === 'liquidity' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Количество топ предметов
                </label>
                <Select
                  label=""
                  options={[
                    { value: '10', label: 'Топ 10' },
                    { value: '50', label: 'Топ 50' },
                    { value: '100', label: 'Топ 100' },
                  ]}
                  value={formData.top_count}
                  onChange={(e) => setFormData({ ...formData, top_count: e.target.value })}
                />
              </div>
            )}

            {generatorMode === 'category' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Категория предметов
                </label>
                <Select
                  label=""
                  options={[
                    { value: 'all', label: 'Все категории' },
                    ...categories.map(c => ({ value: c.key, label: c.name })),
                  ]}
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                />
              </div>
            )}

            {/* Информация */}
            <div className="bg-dark-border rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Как это работает:</h4>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• IQR фильтрация выбросов для точного расчёта медианы</li>
                <li>• Анализ исторических данных за 7 и 30 дней</li>
                <li>• Расчёт тренда цены (рост/падение/стабильно)</li>
                <li>• Оценка ликвидности предмета</li>
                <li>• Взвешенный расчёт справедливой цены</li>
              </ul>
            </div>

            <Button type="submit" className="w-full" isLoading={isLoading}>
              <Download className="h-4 w-4 mr-2" />
              {generatorMode === 'standard' && 'Сгенерировать и скачать конфиг'}
              {generatorMode === 'liquidity' && 'Сгенерировать топ ликвидности'}
              {generatorMode === 'category' && 'Сгенерировать по категории'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
