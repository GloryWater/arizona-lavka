'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Search,
  CheckCircle,
  AlertCircle,
  XCircle,
  Shield,
  User,
  Clock,
  Database,
} from 'lucide-react';
import { adminApi } from '@/shared/api/admin';
import {
  Card,
  CardContent,
  Input,
  Badge,
  Skeleton,
  EmptyState,
  Select,
  Button,
} from '@/shared/ui';

type LogTab = 'audit' | 'admin';

export function AdminLogsPage() {
  const [activeTab, setActiveTab] = useState<LogTab>('audit');
  const [page, setPage] = useState(1);
  
  // Audit logs state
  const [auditSearch, setAuditSearch] = useState('');
  const [auditStatusFilter, setAuditStatusFilter] = useState<string>('');
  const [auditActionFilter, setAuditActionFilter] = useState<string>('');
  const [auditDateFrom, setAuditDateFrom] = useState<string>('');
  const [auditDateTo, setAuditDateTo] = useState<string>('');

  // Admin logs state
  const [adminSearch, setAdminSearch] = useState('');
  const [adminEventTypeFilter, setAdminEventTypeFilter] = useState<string>('');
  const [adminDateFrom, setAdminDateFrom] = useState<string>('');
  const [adminDateTo, setAdminDateTo] = useState<string>('');

  // Загрузка audit логов
  const { data: auditLogs, isLoading: auditLoading } = useQuery({
    queryKey: ['admin-audit-logs', page, auditSearch, auditStatusFilter, auditActionFilter, auditDateFrom, auditDateTo],
    queryFn: () => adminApi.getAuditLogs({
      page,
      limit: 50,
      search_query: auditSearch || undefined,
      status_filter: auditStatusFilter || undefined,
      action: auditActionFilter || undefined,
      date_from: auditDateFrom || undefined,
      date_to: auditDateTo || undefined,
    }),
    staleTime: 1000 * 60 * 2,
    enabled: activeTab === 'audit',
  });

  // Загрузка admin логов
  const { data: adminLogs, isLoading: adminLoading } = useQuery({
    queryKey: ['admin-logs', page, adminSearch, adminEventTypeFilter, adminDateFrom, adminDateTo],
    queryFn: () => adminApi.getLogs({
      page,
      limit: 50,
      search_query: adminSearch || undefined,
      event_type: adminEventTypeFilter || undefined,
      date_from: adminDateFrom || undefined,
      date_to: adminDateTo || undefined,
    }),
    staleTime: 1000 * 60 * 2,
    enabled: activeTab === 'admin',
  });

  const getAuditStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failure':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getAuditStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="success">Успех</Badge>;
      case 'failure':
        return <Badge variant="warning">Ошибка</Badge>;
      case 'error':
        return <Badge variant="destructive">Ошибка</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getAdminEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'login':
      case 'logout':
        return <Shield className="h-4 w-4 text-blue-500" />;
      case 'user_created':
      case 'user_updated':
      case 'user_deleted':
        return <User className="h-4 w-4 text-green-500" />;
      case 'config_generated':
        return <FileText className="h-4 w-4 text-purple-500" />;
      default:
        return <Database className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getAdminEventBadge = (eventType: string) => {
    const badges: Record<string, string> = {
      login: 'primary',
      logout: 'neutral',
      user_created: 'success',
      user_updated: 'info',
      user_deleted: 'destructive',
      config_generated: 'primary',
      settings_updated: 'warning',
      export_data: 'info',
      view_logs: 'neutral',
      view_stats: 'neutral',
    };
    return <Badge variant={(badges[eventType] as any) || 'neutral'}>{eventType}</Badge>;
  };

  return (
    <div className="container max-w-full px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg shadow-green-500/25">
              <FileText className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">Логи системы</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Журнал действий пользователей и админ-панели
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={activeTab === 'audit' ? 'primary' : 'outline'}
          onClick={() => {
            setActiveTab('audit');
            setPage(1);
          }}
          icon={<Shield className="h-4 w-4" />}
        >
          Логи аудита
        </Button>
        <Button
          variant={activeTab === 'admin' ? 'primary' : 'outline'}
          onClick={() => {
            setActiveTab('admin');
            setPage(1);
          }}
          icon={<Database className="h-4 w-4" />}
        >
          Логи админ-панели
        </Button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'audit' ? (
          /* AUDIT LOGS TAB */
          <motion.div
            key="audit"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Filters */}
            <Card className="mb-8">
              <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                  <div className="md:col-span-2">
                    <Input
                      placeholder="Поиск по username, действию..."
                      value={auditSearch}
                      onChange={(e) => {
                        setAuditSearch(e.target.value);
                        setTimeout(() => setPage(1), 500);
                      }}
                      icon={<Search className="h-5 w-5" />}
                    />
                  </div>
                  <div>
                    <Input
                      type="date"
                      value={auditDateFrom}
                      onChange={(e) => {
                        setAuditDateFrom(e.target.value);
                        setTimeout(() => setPage(1), 300);
                      }}
                      label="С даты"
                    />
                  </div>
                  <div>
                    <Input
                      type="date"
                      value={auditDateTo}
                      onChange={(e) => {
                        setAuditDateTo(e.target.value);
                        setTimeout(() => setPage(1), 300);
                      }}
                      label="По дату"
                    />
                  </div>
                  <Select
                    value={auditStatusFilter}
                    onChange={(e) => {
                      setAuditStatusFilter(e.target.value);
                      setTimeout(() => setPage(1), 300);
                    }}
                    label="Статус"
                  >
                    <option value="">Все статусы</option>
                    <option value="success">Успех</option>
                    <option value="failure">Ошибка</option>
                    <option value="error">Ошибка</option>
                  </Select>
                  <Select
                    value={auditActionFilter}
                    onChange={(e) => {
                      setAuditActionFilter(e.target.value);
                      setTimeout(() => setPage(1), 300);
                    }}
                    label="Действие"
                  >
                    <option value="">Все действия</option>
                    <option value="USER_REGISTERED">Регистрация</option>
                    <option value="USER_LOGGED_IN">Вход</option>
                    <option value="CONFIG_GENERATED">Генерация конфига</option>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Logs List */}
            <Card>
              <CardContent className="p-0">
                {auditLoading ? (
                  <div className="p-6 space-y-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-24 w-full" />
                    ))}
                  </div>
                ) : !auditLogs || auditLogs.length === 0 ? (
                  <EmptyState
                    title="Логи аудита не найдены"
                    description={auditSearch ? `Нет логов по запросу "${auditSearch}"` : 'В системе пока нет логов аудита'}
                    icon={<Shield className="h-16 w-16" />}
                  />
                ) : (
                  <div className="divide-y divide-border">
                    {auditLogs.map((log) => (
                      <div
                        key={log.id}
                        className="flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-center space-x-4">
                          <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                            {getAuditStatusIcon(log.status)}
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-foreground">{log.action}</span>
                              {getAuditStatusBadge(log.status)}
                            </div>
                            <div className="flex items-center gap-3 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {log.username || 'Аноним'}
                              </span>
                              {log.resource && (
                                <span className="flex items-center gap-1">
                                  <Shield className="h-3 w-3" />
                                  {log.resource}
                                  {log.resource_id && ` #${log.resource_id}`}
                                </span>
                              )}
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(log.created_at).toLocaleString('ru-RU')}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {log.ip_address && (
                            <Badge variant="neutral" size="sm">{log.ip_address}</Badge>
                          )}
                          {log.error_message && (
                            <Badge variant="destructive" size="sm">Ошибка</Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          /* ADMIN LOGS TAB */
          <motion.div
            key="admin"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Filters */}
            <Card className="mb-8">
              <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  <div className="md:col-span-2">
                    <Input
                      placeholder="Поиск по username или типу события..."
                      value={adminSearch}
                      onChange={(e) => {
                        setAdminSearch(e.target.value);
                        setTimeout(() => setPage(1), 500);
                      }}
                      icon={<Search className="h-5 w-5" />}
                    />
                  </div>
                  <div>
                    <Input
                      type="date"
                      value={adminDateFrom}
                      onChange={(e) => {
                        setAdminDateFrom(e.target.value);
                        setTimeout(() => setPage(1), 300);
                      }}
                      label="С даты"
                    />
                  </div>
                  <div>
                    <Input
                      type="date"
                      value={adminDateTo}
                      onChange={(e) => {
                        setAdminDateTo(e.target.value);
                        setTimeout(() => setPage(1), 300);
                      }}
                      label="По дату"
                    />
                  </div>
                  <Select
                    value={adminEventTypeFilter}
                    onChange={(e) => {
                      setAdminEventTypeFilter(e.target.value);
                      setTimeout(() => setPage(1), 300);
                    }}
                    label="Тип события"
                  >
                    <option value="">Все события</option>
                    <option value="login">Вход</option>
                    <option value="logout">Выход</option>
                    <option value="user_created">Создание пользователя</option>
                    <option value="config_generated">Генерация конфига</option>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Logs List */}
            <Card>
              <CardContent className="p-0">
                {adminLoading ? (
                  <div className="p-6 space-y-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-20 w-full" />
                    ))}
                  </div>
                ) : !adminLogs || adminLogs.length === 0 ? (
                  <EmptyState
                    title="Логи админ-панели не найдены"
                    description={adminSearch ? `Нет логов по запросу "${adminSearch}"` : 'В системе пока нет логов админ-панели'}
                    icon={<Database className="h-16 w-16" />}
                  />
                ) : (
                  <div className="divide-y divide-border">
                    {adminLogs.map((log) => (
                      <div
                        key={log.id}
                        className="flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-center space-x-4">
                          <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                            {getAdminEventIcon(log.event_type)}
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              {getAdminEventBadge(log.event_type)}
                            </div>
                            <div className="flex items-center gap-3 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {log.username || 'Аноним'}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(log.created_at).toLocaleString('ru-RU')}
                              </span>
                              {log.ip_address && (
                                <span className="flex items-center gap-1">
                                  <Shield className="h-3 w-3" />
                                  {log.ip_address}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        {log.details && (
                          <Badge variant="info" size="sm">Детали</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
