'use client';

import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Store,
  TrendingUp,
  TrendingDown,
  Server as ServerIcon,
  Search,
} from 'lucide-react';
import { marketplaceApi } from '@/shared/api';
import { SERVERS } from '@/shared/lib/constants';
import {
  Card,
  CardContent,
  Input,
  Select,
  Badge,
  SkeletonCard,
  EmptyState,
  ErrorState,
} from '@/shared/ui';

export function LavkaListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedServer = searchParams.get('server') || '';
  const searchQuery = searchParams.get('q') || '';

  const { data: lavkasResponse, isLoading, error } = useQuery({
    queryKey: ['lavkas', selectedServer],
    queryFn: async () => {
      if (!selectedServer) return null;
      return marketplaceApi.getLavkas(parseInt(selectedServer));
    },
    enabled: !!selectedServer,
    staleTime: 1000 * 60 * 5,
  });

  const lavkas = lavkasResponse?.lavkas || [];

  const filteredLavkas = lavkas.filter((lavka) =>
    lavka.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getServerName = (id: number) => {
    const server = SERVERS.find((s) => s.id === id);
    return server?.name || 'Неизвестно';
  };

  if (error) {
    return (
      <div className="container max-w-screen-2xl px-4 md:px-6 py-8">
        <ErrorState
          title="Ошибка загрузки"
          description="Не удалось загрузить список лавок"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="container max-w-screen-2xl px-4 md:px-6 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center space-x-4 mb-4">
          <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
            <Store className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">Лавки серверов</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Все активные торговые точки
            </p>
          </div>
        </div>
      </motion.div>

      {/* Filters */}
      <Card className="mb-8">
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Сервер"
              value={selectedServer}
              onChange={(e) => {
                const newParams = new URLSearchParams(searchParams);
                if (e.target.value) {
                  newParams.set('server', e.target.value);
                } else {
                  newParams.delete('server');
                }
                setSearchParams(newParams);
              }}
              icon={<ServerIcon className="h-4 w-4" />}
            >
              <option value="">Все серверы</option>
              {SERVERS.map((server) => (
                <option key={server.id} value={server.id}>
                  {server.name}
                </option>
              ))}
            </Select>

            <Input
              label="Поиск по продавцу"
              placeholder="Никнейм продавца..."
              value={searchQuery}
              onChange={(e) => {
                const newParams = new URLSearchParams(searchParams);
                if (e.target.value) {
                  newParams.set('q', e.target.value);
                } else {
                  newParams.delete('q');
                }
                setSearchParams(newParams);
              }}
              icon={<Search className="h-5 w-5" />}
            />
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      {!selectedServer ? (
        <Card>
          <CardContent>
            <EmptyState
              title="Выберите сервер"
              description="Выберите сервер из списка выше, чтобы увидеть лавки"
              icon={<ServerIcon className="h-16 w-16" />}
            />
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : filteredLavkas && filteredLavkas.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              title="Лавки не найдены"
              description={
                searchQuery
                  ? `Нет лавок с продавцом "${searchQuery}"`
                  : 'На этом сервере пока нет активных лавок'
              }
              icon={<Store className="h-16 w-16" />}
            />
          </CardContent>
        </Card>
      ) : (
        <div>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-foreground flex items-center space-x-3">
                <Store className="h-6 w-6 text-blue-500" />
                <span>
                  {selectedServer ? getServerName(parseInt(selectedServer)) : 'Все серверы'}
                </span>
              </h2>
              <p className="text-muted-foreground mt-1">
                Найдено лавок:{' '}
                <span className="text-blue-500 font-semibold">
                  {filteredLavkas.length || 0}
                </span>
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredLavkas.map((lavka, index) => (
              <motion.div
                key={lavka.lavkaUid}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card hoverable>
                  <CardContent>
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-base font-semibold text-foreground">
                          {lavka.username}
                        </h3>
                        <Badge variant="neutral">#{lavka.lavkaUid.slice(0, 8)}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">ID: {lavka.lavkaUid}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Сервер: {getServerName(lavka.serverId)}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-4">
                      <div className="text-center p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                        <div className="text-xl font-bold text-blue-500">{lavka.buyCount}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <TrendingUp className="h-3 w-3 inline mr-1" />
                          Скупка
                        </div>
                      </div>
                      <div className="text-center p-3 rounded-xl bg-green-500/10 border border-green-500/20">
                        <div className="text-xl font-bold text-green-500">{lavka.sellCount}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <TrendingDown className="h-3 w-3 inline mr-1" />
                          Продажа
                        </div>
                      </div>
                    </div>

                    <div className="text-sm text-muted-foreground mb-4 flex items-center justify-between">
                      <span>Всего предметов:</span>
                      <span className="text-foreground font-semibold">{lavka.totalItems}</span>
                    </div>

                    <Link
                      to={`/lavka/${lavka.lavkaUid}?server_id=${selectedServer}`}
                      className="block bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-center py-2.5 rounded-lg font-semibold transition-all"
                    >
                      <div className="flex items-center justify-center space-x-2">
                        <Store className="h-4 w-4" />
                        <span>Открыть лавку</span>
                      </div>
                    </Link>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
