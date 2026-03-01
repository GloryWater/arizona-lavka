'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Settings,
  Download,
  Server,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Loader2,
  Copy,
  ClipboardCheck,
  Database,
  ListFilter,
  Layers,
} from 'lucide-react';
import { configApi } from '@/shared/api';
import { useToast } from '@/shared/ui/Toast';
import type { ConfigMode, ConfigGenerateResponse, ConfigGenerationType } from '@/shared/types';
import { SERVERS } from '@/shared/lib/constants';
import {
  Card,
  CardContent,
  Button,
  Select,
  Badge,
  EmptyState,
  Alert,
  CategoryBlock,
  Input,
} from '@/shared/ui';

export function ConfigGeneratorPage() {
  const toast = useToast();
  
  // Основные параметры
  const [selectedServer, setSelectedServer] = useState<string>('');
  const [mode, setMode] = useState<ConfigMode>('SELL');
  const [percentage, setPercentage] = useState<number>(-5);
  
  // Способ генерации
  const [generationType, setGenerationType] = useState<ConfigGenerationType>('all');
  const [topCount, setTopCount] = useState<number>(20);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  
  // Результаты
  const [generatedConfig, setGeneratedConfig] = useState<unknown[]>([]);
  const [isCopied, setIsCopied] = useState(false);

  // Загрузка категорий
  const { data: categories } = useQuery({
    queryKey: ['config-categories'],
    queryFn: () => configApi.getCategories(),
    staleTime: 1000 * 60 * 30,
  });

  // Загрузка настроек генерации
  const { data: generationSettings } = useQuery({
    queryKey: ['config-generation-settings'],
    queryFn: async () => {
      try {
        const settings = await configApi.getSettings();
        const configSetting = settings.find(s => s.key === 'config_generation_methods');
        return configSetting?.value || { allow_all: true, allow_liquidity: true, allow_category: true };
      } catch {
        return { allow_all: true, allow_liquidity: true, allow_category: true };
      }
    },
    staleTime: 1000 * 60 * 5,
  });

  // Генерация конфига
  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedServer) throw new Error('Выберите сервер');
      
      const serverId = parseInt(selectedServer);
      
      switch (generationType) {
        case 'all':
          return configApi.generateAll(serverId, mode, percentage);
        case 'liquidity':
          return configApi.generateByLiquidity(serverId, mode, percentage, topCount);
        case 'category':
          if (!selectedCategory) throw new Error('Выберите категорию');
          return configApi.generateByCategory(serverId, mode, percentage, selectedCategory);
        default:
          throw new Error('Неизвестный тип генерации');
      }
    },
    onSuccess: (data: ConfigGenerateResponse) => {
      const configData = data.config || [];
      setGeneratedConfig(configData);
      toast.success(
        `Сгенерировано ${data.total_items || configData.length} предметов`,
        'Конфиг готов'
      );
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Не удалось сгенерировать конфиг', 'Ошибка');
    },
  });

  const handleCopy = async () => {
    if (generatedConfig.length === 0) return;
    
    try {
      const json = JSON.stringify(generatedConfig, null, 2);
      await navigator.clipboard.writeText(json);
      setIsCopied(true);
      toast.success('Конфиг скопирован в буфер обмена');
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      toast.error('Не удалось скопировать конфиг', 'Ошибка');
    }
  };

  const handleDownload = async () => {
    if (!selectedServer || generatedConfig.length === 0) return;

    try {
      const serverId = parseInt(selectedServer);
      let result: { data: Blob; filename?: string };

      switch (generationType) {
        case 'all':
          result = await configApi.downloadGenerated(serverId, mode, percentage);
          break;
        case 'liquidity':
          result = await configApi.downloadByLiquidity(serverId, mode, percentage, topCount);
          break;
        case 'category':
          if (!selectedCategory) throw new Error('Выберите категорию');
          result = await configApi.downloadByCategory(serverId, mode, percentage, selectedCategory);
          break;
        default:
          throw new Error('Неизвестный тип генерации');
      }

      const { data: blob, filename } = result;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `config_${mode.toLowerCase()}_${selectedServer}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('Файл скачан в кодировке cp1251', 'Загрузка завершена');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Не удалось скачать конфиг', 'Ошибка');
    }
  };

  const getServerName = (id: string) => {
    const server = SERVERS.find((s) => s.id.toString() === id);
    return server?.name || 'Неизвестно';
  };

  const getPercentageHint = () => {
    if (percentage === 0) {
      return 'Предметы будут иметь рыночную цену';
    } else if (percentage < 0) {
      return `Цена каждого предмета уменьшится на ${Math.abs(percentage)}%`;
    } else {
      return `Цена каждого предмета увеличится на ${percentage}%`;
    }
  };

  const isGenerateDisabled = !selectedServer || 
    (generationType === 'category' && !selectedCategory) ||
    generateMutation.isPending;

  const generationMethods = [
    {
      id: 'all' as const,
      title: 'Все предметы',
      description: 'Генерация конфига со всеми предметами, доступными на выбранном сервере. Подходит для создания полной торговой сети.',
      icon: <Database className="h-6 w-6" />,
      color: 'from-blue-500 to-cyan-500',
      disabled: !(generationSettings as any)?.allow_all,
    },
    {
      id: 'liquidity' as const,
      title: 'По ликвидности',
      description: 'Генерация топ-N самых ликвидных предметов. Идеально для быстрой торговли с высоким оборотом.',
      icon: <TrendingUp className="h-6 w-6" />,
      color: 'from-green-500 to-emerald-500',
      disabled: !(generationSettings as any)?.allow_liquidity,
    },
    {
      id: 'category' as const,
      title: 'По категориям',
      description: 'Генерация предметов определённой категории. Позволяет специализироваться на конкретных типах товаров.',
      icon: <ListFilter className="h-6 w-6" />,
      color: 'from-purple-500 to-pink-500',
      disabled: !(generationSettings as any)?.allow_category,
    },
  ];

  return (
    <div className="container max-w-screen-2xl px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <Settings className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">
                Генератор конфигов
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Автоматическая генерация конфигов для торговых автоматов
              </p>
            </div>
          </div>
        </div>

        {/* Generator Form */}
        <Card className="mb-8">
          <CardContent className="p-6">
            {/* Способ генерации - карточки */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                <Layers className="h-4 w-4" />
                Способ генерации
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {generationMethods.map((method) => (
                  <button
                    key={method.id}
                    type="button"
                    disabled={method.disabled}
                    onClick={() => setGenerationType(method.id)}
                    className={`
                      relative p-4 rounded-xl border-2 transition-all duration-200 text-left
                      ${generationType === method.id
                        ? `border-${method.color.split(' ')[0]} bg-${method.color.split(' ')[0]}/5`
                        : 'border-border hover:border-primary/50'
                      }
                      ${method.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${method.color} flex items-center justify-center mb-3`}>
                      <div className="text-white">
                        {method.icon}
                      </div>
                    </div>
                    <h4 className="font-semibold text-foreground mb-1">{method.title}</h4>
                    <p className="text-sm text-muted-foreground">{method.description}</p>
                    {generationType === method.id && (
                      <div className="absolute top-3 right-3">
                        <CheckCircle className={`h-5 w-5 text-${method.color.split(' ')[0]}`} />
                      </div>
                    )}
                    {method.disabled && (
                      <div className="absolute inset-0 bg-background/80 rounded-xl flex items-center justify-center">
                        <Badge variant="neutral">Отключено</Badge>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Выбор топ-N для ликвидности */}
            {generationType === 'liquidity' && (
              <div className="mb-6">
                <Select
                  label="Количество предметов"
                  value={topCount.toString()}
                  onChange={(e) => setTopCount(parseInt(e.target.value))}
                  icon={<TrendingUp className="h-4 w-4" />}
                >
                  <option value="10">Топ-10</option>
                  <option value="20">Топ-20</option>
                  <option value="50">Топ-50</option>
                  <option value="100">Топ-100</option>
                </Select>
              </div>
            )}

            {/* Категории */}
            {generationType === 'category' && categories && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-foreground mb-3">
                  Выберите категорию
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {categories.map((category, index) => (
                    <CategoryBlock
                      key={category.key}
                      name={category.name}
                      selected={selectedCategory === index.toString()}
                      onClick={() => setSelectedCategory(index.toString())}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Параметры генерации */}
            <div className="border-t border-border pt-6 mt-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Параметры генерации
              </h2>

              {/* Основные параметры */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Select
                  label="Сервер"
                  value={selectedServer}
                  onChange={(e) => setSelectedServer(e.target.value)}
                  icon={<Server className="h-4 w-4" />}
                >
                  <option value="">Выберите сервер</option>
                  {SERVERS.map((server) => (
                    <option key={server.id} value={server.id}>
                      {server.name}
                    </option>
                  ))}
                </Select>

                <Select
                  label="Режим"
                  value={mode}
                  onChange={(e) => setMode(e.target.value as ConfigMode)}
                  icon={mode === 'SELL' ? <TrendingDown className="h-4 w-4" /> : <TrendingUp className="h-4 w-4" />}
                >
                  <option value="SELL">Продажа (SELL)</option>
                  <option value="BUY">Скупка (BUY)</option>
                </Select>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Корректировка цены (%)
                  </label>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      min="-50"
                      max="50"
                      value={percentage.toString()}
                      onChange={(e) => setPercentage(parseInt(e.target.value) || 0)}
                      className="flex-1"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(-25)}
                      className="text-xs"
                    >
                      −25%
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(-10)}
                      className="text-xs"
                    >
                      −10%
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(-5)}
                      className="text-xs"
                    >
                      −5%
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(0)}
                      className="text-xs"
                    >
                      0%
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(5)}
                      className="text-xs"
                    >
                      +5%
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(10)}
                      className="text-xs"
                    >
                      +10%
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setPercentage(25)}
                      className="text-xs"
                    >
                      +25%
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground px-1">
                    {getPercentageHint()}
                  </p>
                </div>
              </div>
            </div>

            {/* Кнопка генерации */}
            <div className="flex items-center justify-between">
              <Alert
                variant="info"
                description="Конфиг будет сгенерирован на основе текущих рыночных цен"
                className="flex-1 mr-4"
              />
              <Button
                onClick={() => generateMutation.mutate()}
                isLoading={generateMutation.isPending}
                disabled={isGenerateDisabled}
                icon={
                  generateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Settings className="h-4 w-4" />
                  )
                }
              >
                {generateMutation.isPending ? 'Генерация...' : 'Сгенерировать'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {generatedConfig.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">
                      Результат генерации
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      Сервер: {getServerName(selectedServer)} • Режим:{' '}
                      {mode === 'SELL' ? 'Продажа' : 'Скупка'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="success">
                      <CheckCircle className="h-3 w-3" />
                      {generatedConfig.length} предметов
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopy}
                      icon={isCopied ? <ClipboardCheck className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    >
                      {isCopied ? 'Скопировано' : 'Копировать'}
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleDownload}
                      icon={<Download className="h-4 w-4" />}
                    >
                      Скачать
                    </Button>
                  </div>
                </div>

                {/* Preview */}
                <div className="border border-border rounded-lg bg-muted/30 p-4 max-h-96 overflow-auto">
                  <pre className="text-xs text-foreground font-mono">
                    {JSON.stringify(generatedConfig.slice(0, 5), null, 2)}
                    {generatedConfig.length > 5 && (
                      <div className="text-center text-muted-foreground py-2">
                        ... и ещё {generatedConfig.length - 5} предметов
                      </div>
                    )}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Empty State */}
        {!selectedServer && generatedConfig.length === 0 && (
          <Card>
            <CardContent>
              <EmptyState
                title="Начните генерацию"
                description="Выберите сервер и настройте параметры для генерации конфига"
                icon={<Settings className="h-16 w-16" />}
              />
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
