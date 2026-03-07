'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  FileText,
  Settings,
  TrendingUp,
  Activity,
  Shield,
  Calendar,
  Download,
} from 'lucide-react';
import { adminApi, type StatsChartData } from '@/shared/api/admin';
import { useToast } from '@/shared/ui/Toast';
import {
  Card,
  CardContent,
  Skeleton,
  Alert,
  Button,
  Input,
} from '@/shared/ui';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

export function AdminDashboard() {
  const toast = useToast();
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Загрузка статистики
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
    staleTime: 1000 * 60 * 5,
  });

  // Загрузка данных графиков
  const { data: chartData, isLoading: chartsLoading } = useQuery<StatsChartData[]>({
    queryKey: ['admin-stats-charts', startDate, endDate],
    queryFn: () => adminApi.getStatsChartData({
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
    staleTime: 1000 * 60 * 5,
  });

  const statCards = [
    {
      title: 'Всего пользователей',
      value: stats?.total_users ?? 0,
      icon: <Users className="h-5 w-5 text-blue-500" />,
      bg: 'bg-blue-500/10',
    },
    {
      title: 'Всего конфигов',
      value: stats?.total_configs ?? 0,
      icon: <FileText className="h-5 w-5 text-green-500" />,
      bg: 'bg-green-500/10',
    },
    {
      title: 'DAU (за сегодня)',
      value: stats?.dau ?? 0,
      icon: <Activity className="h-5 w-5 text-purple-500" />,
      bg: 'bg-purple-500/10',
    },
    {
      title: 'MAU (за 30 дней)',
      value: stats?.mau ?? 0,
      icon: <TrendingUp className="h-5 w-5 text-orange-500" />,
      bg: 'bg-orange-500/10',
    },
    {
      title: 'Конфигов на пользователя/день',
      value: stats?.avg_configs_per_user_per_day?.toFixed(2) ?? '0.00',
      icon: <Settings className="h-5 w-5 text-cyan-500" />,
      bg: 'bg-cyan-500/10',
    },
  ];

  const handleExportUsers = async () => {
    try {
      const blob = await adminApi.exportUsers('csv');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Пользователи экспортированы в CSV', 'Успешно');
    } catch (error) {
      toast.error('Не удалось экспортировать пользователей', 'Ошибка');
    }
  };

  return (
    <div className="container max-w-full px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">Админ-панель</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Панель управления Arizona Lavka Marketplace
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={handleExportUsers}
            icon={<Download className="h-4 w-4" />}
            className="hover:shadow-md transition-all duration-200"
          >
            Экспорт пользователей
          </Button>
        </div>
      </motion.div>

      <Alert
        variant="info"
        title="Информация"
        description="Добро пожаловать в админ-панель. Используйте меню для навигации."
        className="mb-8"
      />

      {/* Stats Grid - Improved responsive layout */}
      <div className="grid grid-cols-1 xs:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 sm:gap-6 mb-8">
        {statCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card variant="outlined" className="border-border/50 hover:border-primary/30 hover:shadow-lg transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${card.bg}`}>
                    {card.icon}
                  </div>
                  <div>
                    {statsLoading ? (
                      <>
                        <Skeleton className="h-4 w-24 mb-1" />
                        <Skeleton className="h-8 w-16" />
                      </>
                    ) : (
                      <>
                        <p className="text-xs text-muted-foreground">{card.title}</p>
                        <p className="text-2xl font-bold text-foreground">{card.value}</p>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-8">
        {/* Registrations Chart */}
        <Card>
          <CardContent className="p-4 sm:p-6">
            <h2 className="text-base sm:text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Users className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500" />
              Регистрации по дням
            </h2>
            {chartsLoading ? (
              <Skeleton className="h-48 sm:h-64 w-full" />
            ) : chartData && chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      borderColor: 'hsl(var(--border))',
                      borderRadius: 'var(--radius-sm)',
                    }}
                    labelStyle={{
                      color: 'hsl(var(--foreground))',
                    }}
                    itemStyle={{
                      color: 'hsl(var(--foreground))',
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="registrations" stroke="#3b82f6" name="Регистрации" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-48 sm:h-64 flex items-center justify-center text-muted-foreground">
                Нет данных для отображения
              </div>
            )}
          </CardContent>
        </Card>

        {/* Configs Chart */}
        <Card>
          <CardContent className="p-4 sm:p-6">
            <h2 className="text-base sm:text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-green-500" />
              Генерации конфигов по дням
            </h2>
            {chartsLoading ? (
              <Skeleton className="h-48 sm:h-64 w-full" />
            ) : chartData && chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      borderColor: 'hsl(var(--border))',
                      borderRadius: 'var(--radius-sm)',
                    }}
                    labelStyle={{
                      color: 'hsl(var(--foreground))',
                    }}
                    itemStyle={{
                      color: 'hsl(var(--foreground))',
                    }}
                  />
                  <Legend />
                  <Bar dataKey="configs_generated" fill="#22c55e" name="Конфиги" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-48 sm:h-64 flex items-center justify-center text-muted-foreground">
                Нет данных для отображения
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Date Filter - Improved responsive layout */}
      <Card className="mb-8">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-3 sm:gap-4">
            <div className="flex-1 w-full sm:min-w-[180px]">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                label="Начальная дата"
              />
            </div>
            <div className="flex-1 w-full sm:min-w-[180px]">
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                label="Конечная дата"
              />
            </div>
            <Button
              variant="primary"
              icon={<Calendar className="h-4 w-4" />}
              className="w-full sm:w-auto"
            >
              Применить фильтр
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setStartDate('');
                setEndDate('');
              }}
              className="w-full sm:w-auto"
            >
              Сбросить
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">Быстрые действия</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/admin/users"
              className="p-4 rounded-lg border border-border hover:bg-accent transition-colors"
            >
              <Users className="h-6 w-6 text-blue-500 mb-2" />
              <h3 className="font-medium text-foreground">Управление пользователями</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Просмотр и редактирование пользователей
              </p>
            </a>
            <a
              href="/admin/logs"
              className="p-4 rounded-lg border border-border hover:bg-accent transition-colors"
            >
              <FileText className="h-6 w-6 text-green-500 mb-2" />
              <h3 className="font-medium text-foreground">Логи системы</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Просмотр логов и аудита
              </p>
            </a>
            <a
              href="/admin/settings"
              className="p-4 rounded-lg border border-border hover:bg-accent transition-colors"
            >
              <Settings className="h-6 w-6 text-orange-500 mb-2" />
              <h3 className="font-medium text-foreground">Настройки</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Глобальные настройки системы
              </p>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
