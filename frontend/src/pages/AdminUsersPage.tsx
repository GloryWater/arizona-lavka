'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users,
  Search,
  Shield,
  Download,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  MoreVertical,
  Ban,
} from 'lucide-react';
import { adminApi } from '@/shared/api/admin';
import { useToast } from '@/shared/ui/Toast';
import type { AdminUser } from '@/shared/types';
import {
  Card,
  CardContent,
  Input,
  Badge,
  Skeleton,
  EmptyState,
  Button,
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  Alert,
} from '@/shared/ui';

type SortField = 'id' | 'username' | 'created_at' | 'configs_count';
type SortOrder = 'asc' | 'desc';

export function AdminUsersPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  
  // Состояния
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [banDialogOpen, setBanDialogOpen] = useState(false);
  const [banReason, setBanReason] = useState('');

  // Загрузка пользователей
  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users', page, search, sortField, sortOrder],
    queryFn: () => adminApi.getUsers({
      page,
      limit: 100,
      search: search || undefined,
      sort_by: sortField,
    }),
    staleTime: 1000 * 60 * 2,
  });

  // Мутация для бана
  const banMutation = useMutation({
    mutationFn: async (_userId: number) => {
      // TODO: Реализовать endpoint бана на backend
      await new Promise(resolve => setTimeout(resolve, 500));
      return { message: 'User banned' };
    },
    onSuccess: () => {
      toast.success('Пользователь заблокирован', 'Успешно');
      setBanDialogOpen(false);
      setBanReason('');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: () => {
      toast.error('Не удалось заблокировать пользователя', 'Ошибка');
    },
  });

  // Экспорт
  const handleExport = async () => {
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
    } catch {
      toast.error('Не удалось экспортировать', 'Ошибка');
    }
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const handleSearch = () => {
    setPage(1);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className="w-4 h-4" />;
    return sortOrder === 'asc' 
      ? <ChevronUp className="w-4 h-4" /> 
      : <ChevronDown className="w-4 h-4" />;
  };

  return (
    <div className="container max-w-screen-2xl px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <Users className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">Пользователи</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Управление пользователями системы
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={handleExport}
            icon={<Download className="h-4 w-4" />}
          >
            Скачать CSV
          </Button>
        </div>
      </motion.div>

      {/* Search */}
      <Card className="mb-8">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Поиск по ID или логину..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                icon={<Search className="h-5 w-5" />}
              />
            </div>
            <Button onClick={handleSearch} variant="primary">
              Поиск
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : !users || users.length === 0 ? (
            <EmptyState
              title="Пользователи не найдены"
              description={search ? `Нет пользователей по запросу "${search}"` : 'В системе пока нет пользователей'}
              icon={<Users className="h-16 w-16" />}
            />
          ) : (
            <>
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 p-4 bg-muted/50 border-b border-border text-sm font-medium text-muted-foreground">
                <div className="col-span-1 flex items-center gap-1 cursor-pointer hover:text-foreground" onClick={() => handleSort('id')}>
                  ID <SortIcon field="id" />
                </div>
                <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-foreground" onClick={() => handleSort('username')}>
                  Логин <SortIcon field="username" />
                </div>
                <div className="col-span-3">Email</div>
                <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-foreground" onClick={() => handleSort('created_at')}>
                  Дата регистрации <SortIcon field="created_at" />
                </div>
                <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-foreground" onClick={() => handleSort('configs_count')}>
                  Конфигов <SortIcon field="configs_count" />
                </div>
                <div className="col-span-1">Статус</div>
                <div className="col-span-1">Действия</div>
              </div>

              {/* Table Body */}
              <div className="divide-y divide-border">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="grid grid-cols-12 gap-4 p-4 hover:bg-accent/50 transition-colors items-center"
                  >
                    <div className="col-span-1 text-sm text-foreground">#{user.id}</div>
                    <div className="col-span-2">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-sm font-medium">
                          {user.username.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-foreground">{user.username}</span>
                      </div>
                    </div>
                    <div className="col-span-3">
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-sm text-muted-foreground">
                        {new Date(user.created_at).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                    <div className="col-span-2">
                      <Badge variant="primary">{user.configs_count || 0}</Badge>
                    </div>
                    <div className="col-span-1">
                      <Badge variant={user.role === 'admin' ? 'destructive' : 'neutral'}>
                        {user.role === 'admin' ? 'Admin' : 'User'}
                      </Badge>
                    </div>
                    <div className="col-span-1">
                      <div className="relative">
                        <Button
                          variant="ghost"
                          size="icon"
                          icon={<MoreVertical className="h-4 w-4" />}
                          onClick={() => setSelectedUser(user)}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between p-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Страница {page} (показано {users.length})
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    icon={<ChevronLeft className="h-4 w-4" />}
                  >
                    Назад
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={users.length < 100}
                    icon={<ChevronRight className="h-4 w-4" />}
                  >
                    Вперед
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* User Actions Dialog */}
      <Dialog open={!!selectedUser} onOpenChange={() => setSelectedUser(null)}>
        <DialogContent>
          <DialogHeader>
            <h2 className="text-xl font-semibold">Пользователь #{selectedUser?.id}</h2>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-lg font-medium">
                {selectedUser?.username.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="font-medium text-foreground">{selectedUser?.username}</p>
                <p className="text-sm text-muted-foreground">{selectedUser?.email}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Роль</p>
                <Badge variant={selectedUser?.role === 'admin' ? 'destructive' : 'neutral'}>
                  {selectedUser?.role === 'admin' ? 'Администратор' : 'Пользователь'}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Конфигов</p>
                <p className="font-medium">{selectedUser?.configs_count || 0}</p>
              </div>
            </div>
            <Alert
              variant="info"
              description={`Зарегистрирован ${new Date(selectedUser?.created_at || '').toLocaleDateString('ru-RU')}`}
            />
          </div>
          <DialogFooter className="gap-2">
            {selectedUser?.role === 'admin' ? (
              <Button
                variant="outline"
                onClick={() => {
                  // TODO: Remove admin role
                  toast.info('Функция в разработке');
                }}
                icon={<Shield className="h-4 w-4" />}
              >
                Снять админа
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => {
                  // TODO: Make admin
                  toast.info('Функция в разработке');
                }}
                icon={<Shield className="h-4 w-4" />}
              >
                Сделать админом
              </Button>
            )}
            <Button
              variant="destructive"
              onClick={() => setBanDialogOpen(true)}
              icon={<Ban className="h-4 w-4" />}
            >
              Заблокировать
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Ban Dialog */}
      <Dialog open={banDialogOpen} onOpenChange={setBanDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <h2 className="text-xl font-semibold">Заблокировать пользователя</h2>
            <p className="text-sm text-muted-foreground">
              Вы уверены, что хотите заблокировать {selectedUser?.username}?
            </p>
          </DialogHeader>
          <div className="py-4">
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Причина блокировки
            </label>
            <textarea
              className="w-full h-32 p-3 text-sm bg-background rounded-lg border border-input focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Например: спам, нарушение правил..."
              value={banReason}
              onChange={(e) => setBanReason(e.target.value)}
            />
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setBanDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedUser && banMutation.mutate(selectedUser.id)}
              isLoading={banMutation.isPending}
              icon={<Ban className="h-4 w-4" />}
            >
              Заблокировать
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
