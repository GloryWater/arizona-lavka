/**
 * AdminMetricsPage - страница админ-дашборда с метриками.
 *
 * Показывает:
 * - Обзор метрик (DAU, MAU, сессии, события)
 * - Метрики вовлеченности
 * - Метрики конверсий
 * - Сегменты пользователей
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import { useAuthStore } from '@/features/auth/model/useAuthStore';

// ============================================================================
// TYPES
// ============================================================================

interface MetricsOverview {
  dau: number;
  mau: number;
  avg_session_duration: number;
  total_sessions_24h: number;
  total_events_24h: number;
  total_page_views_24h: number;
  total_conversions_24h: number;
  total_revenue_24h: number;
}

interface EngagementMetrics {
  top_pages: Array<{ page_path: string; count: number }>;
  top_actions: Array<{ event_type: string; count: number }>;
  retention_rate: number;
  avg_pages_per_session: number;
}

interface ConversionMetrics {
  total_conversions: number;
  conversion_funnel: Array<{ type: string; count: number; total_value: number }>;
  revenue_metrics: {
    total: number;
    avg: number;
    by_type: Record<string, number>;
  };
}

interface UserSegments {
  total_users: number;
  active_users: number;
  power_users: Array<{ user_id: number; username: string; events_count: number }>;
  user_segments: Record<string, number>;
}

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * Карточка с метрикой.
 */
function MetricCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="bg-card rounded-lg shadow p-6 border border-border">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      <div className="text-3xl font-bold text-foreground mb-1">{value}</div>
      {subtitle && <div className="text-xs text-muted-foreground">{subtitle}</div>}
    </div>
  );
}

/**
 * Таблица с данными.
 */
function DataTable({
  title,
  columns,
  data,
}: {
  title: string;
  columns: Array<{ key: string; header: string }>;
  data: Record<string, unknown>[];
}) {
  return (
    <div className="bg-card rounded-lg shadow border border-border overflow-hidden">
      <div className="px-6 py-4 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider"
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-muted/30 transition-colors">
                {columns.map((col) => (
                  <td key={col.key} className="px-6 py-4 text-sm text-foreground">
                    {row[col.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Selector диапазона дат.
 */
function DateRangeSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const ranges = [
    { label: '24 часа', value: '24h' },
    { label: '7 дней', value: '7d' },
    { label: '30 дней', value: '30d' },
    { label: '90 дней', value: '90d' },
  ];

  return (
    <div className="flex gap-2">
      {ranges.map((range) => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`px-4 py-2 text-sm rounded-lg transition-colors ${
            value === range.value
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function AdminMetricsPage() {
  const { isAdmin } = useAuthStore();
  const [dateRange, setDateRange] = useState('30d');

  // Проверка доступа
  if (!isAdmin) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground mb-2">Доступ запрещён</h1>
          <p className="text-muted-foreground">Требуется роль администратора</p>
        </div>
      </div>
    );
  }

  // Загрузка данных
  const { data: overview, isLoading: overviewLoading } = useQuery<MetricsOverview>({
    queryKey: ['metrics', 'overview', dateRange],
    queryFn: () => apiClient.get(`/v1/admin/metrics/overview?range=${dateRange}`),
    refetchInterval: 60000, // Обновлять каждую минуту
  });

  const { data: engagement, isLoading: engagementLoading } = useQuery<EngagementMetrics>({
    queryKey: ['metrics', 'engagement', dateRange],
    queryFn: () => apiClient.get(`/v1/admin/metrics/engagement?range=${dateRange}`),
  });

  const { data: conversions, isLoading: conversionsLoading } = useQuery<ConversionMetrics>({
    queryKey: ['metrics', 'conversions', dateRange],
    queryFn: () => apiClient.get(`/v1/admin/metrics/conversions?range=${dateRange}`),
  });

  const { data: segments, isLoading: segmentsLoading } = useQuery<UserSegments>({
    queryKey: ['metrics', 'users', dateRange],
    queryFn: () => apiClient.get(`/v1/admin/metrics/users?range=${dateRange}`),
  });

  const isLoading = overviewLoading || engagementLoading || conversionsLoading || segmentsLoading;

  // Экспорт данных
  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const url = `/v1/admin/metrics/export${format === 'json' ? '/json' : ''}?range=${dateRange}`;
      const response = await apiClient.get(url);
      // Создаём ссылку для скачивания
      const blob = new Blob([JSON.stringify(response)], { type: 'application/json' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `metrics_${dateRange}_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">Загрузка метрик...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Метрики</h1>
          <p className="text-muted-foreground">
            Дашборд аналитики пользователей и конверсий
          </p>
        </div>
        <div className="flex items-center gap-4">
          <DateRangeSelector value={dateRange} onChange={setDateRange} />
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Экспорт CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 transition-colors"
          >
            Экспорт JSON
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="DAU (Active Users Today)"
          value={overview?.dau ?? 0}
          subtitle="Уникальных пользователей за сегодня"
        />
        <MetricCard
          title="MAU (Monthly Users)"
          value={overview?.mau ?? 0}
          subtitle="Уникальных пользователей за 30 дней"
        />
        <MetricCard
          title="Avg Session Duration"
          value={`${Math.round((overview?.avg_session_duration ?? 0) / 60)}m ${Math.round(overview?.avg_session_duration ?? 0) % 60}s`}
          subtitle="Средняя длительность сессии"
        />
        <MetricCard
          title="Total Revenue (24h)"
          value={`${(overview?.total_revenue_24h ?? 0).toFixed(2)} ₽`}
          subtitle="Выручка за 24 часа"
        />
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Sessions (24h)"
          value={overview?.total_sessions_24h ?? 0}
        />
        <MetricCard
          title="Page Views (24h)"
          value={overview?.total_page_views_24h ?? 0}
        />
        <MetricCard
          title="Events (24h)"
          value={overview?.total_events_24h ?? 0}
        />
        <MetricCard
          title="Conversions (24h)"
          value={overview?.total_conversions_24h ?? 0}
        />
      </div>

      {/* Engagement Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DataTable
          title="📄 Топ страниц"
          columns={[
            { key: 'page_path', header: 'Страница' },
            { key: 'count', header: 'Просмотры' },
          ]}
          data={engagement?.top_pages ?? []}
        />
        <DataTable
          title="⚡ Топ действий"
          columns={[
            { key: 'event_type', header: 'Событие' },
            { key: 'count', header: 'Количество' },
          ]}
          data={engagement?.top_actions ?? []}
        />
      </div>

      {/* Conversion Funnel */}
      <DataTable
        title="💰 Воронка конверсий"
        columns={[
          { key: 'type', header: 'Тип' },
          { key: 'count', header: 'Количество' },
          { key: 'total_value', header: 'Сумма (₽)' },
        ]}
        data={conversions?.conversion_funnel.map((item) => ({
          ...item,
          total_value: item.total_value.toFixed(2),
        })) ?? []}
      />

      {/* User Segments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-lg shadow p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">Сегменты пользователей</h3>
          <div className="space-y-3">
            {Object.entries(segments?.user_segments ?? {}).map(([segment, count]) => (
              <div key={segment} className="flex items-center justify-between">
                <span className="text-muted-foreground capitalize">{segment.replace(/_/g, ' ')}</span>
                <span className="text-lg font-semibold text-foreground">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <DataTable
          title="🌟 Power Users (Top 10)"
          columns={[
            { key: 'username', header: 'Пользователь' },
            { key: 'events_count', header: 'События' },
          ]}
          data={segments?.power_users ?? []}
        />
      </div>

      {/* Retention Info */}
      <div className="bg-card rounded-lg shadow p-6 border border-border">
        <h3 className="text-lg font-semibold text-foreground mb-4">Общая статистика</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <div className="text-sm text-muted-foreground mb-1">Всего пользователей</div>
            <div className="text-2xl font-bold text-foreground">{segments?.total_users ?? 0}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Активных пользователей</div>
            <div className="text-2xl font-bold text-foreground">{segments?.active_users ?? 0}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Retention Rate</div>
            <div className="text-2xl font-bold text-foreground">
              {(engagement?.retention_rate ?? 0).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground mb-1">Avg Pages/Session</div>
            <div className="text-2xl font-bold text-foreground">
              {(engagement?.avg_pages_per_session ?? 0).toFixed(1)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminMetricsPage;
