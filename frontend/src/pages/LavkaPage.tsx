'use client';

import { useParams, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Store,
  TrendingUp,
  TrendingDown,
  ArrowLeft
} from 'lucide-react';
import { marketplaceApi } from '@/shared/api';
import { SERVERS } from '@/shared/lib/constants';
import { formatPrice } from '@/shared/lib/helpers';
import {
  Card,
  CardContent,
  Button,
  Badge,
  Skeleton,
  EmptyState,
  ErrorState,
} from '@/shared/ui';

export function LavkaPage() {
  const { lavkaUid } = useParams<{ lavkaUid: string }>();
  const [searchParams] = useSearchParams();
  const serverId = searchParams.get('server_id');

  const { data: lavka, isLoading, error } = useQuery({
    queryKey: ['lavka', lavkaUid, serverId],
    queryFn: async () => {
      if (!lavkaUid || !serverId) throw new Error('Missing parameters');
      return marketplaceApi.getLavkaDetail(lavkaUid, parseInt(serverId));
    },
    enabled: !!lavkaUid && !!serverId,
    staleTime: 1000 * 60 * 2,
  });

  // Вычисляем serverName из serverId
  const serverName = lavka && serverId 
    ? (SERVERS.find(s => s.id.toString() === serverId)?.name || 'Unknown')
    : 'Unknown';

  if (error) {
    return (
      <div className="container max-w-screen-3xl px-4 md:px-6 py-8">
        <ErrorState
          title="Ошибка загрузки"
          description="Не удалось загрузить информацию о лавке"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (isLoading || !lavka) {
    return (
      <div className="container max-w-screen-3xl px-4 md:px-6 py-8" data-testid="lavka-loading">
        <div className="mb-6">
          <Button variant="ghost" onClick={() => window.history.back()} icon={<ArrowLeft className="h-4 w-4" />}>
            Назад
          </Button>
        </div>
        <div className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-4 mb-6">
                <Skeleton className="h-16 w-16 rounded-full" data-testid="skeleton" />
                <div className="flex-1">
                  <Skeleton className="h-6 w-48 mb-2" data-testid="skeleton" />
                  <Skeleton className="h-4 w-32" data-testid="skeleton" />
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 rounded-xl" data-testid="skeleton" />
                ))}
              </div>
            </CardContent>
          </Card>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" data-testid="skeleton" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-screen-3xl px-4 md:px-6 py-8">
      {/* Back button */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="mb-6"
      >
        <Button
          variant="ghost"
          onClick={() => window.history.back()}
          icon={<ArrowLeft className="h-4 w-4" />}
        >
          Назад
        </Button>
      </motion.div>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
              <div className="flex items-center space-x-4">
                <div className="h-16 w-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <Store className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-foreground">{lavka.username}</h1>
                  <p className="text-sm text-muted-foreground">
                    UID: {lavka.lavkaUid} • {serverName}
                  </p>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card variant="outlined">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-blue-500">{lavka.totalBuy}</div>
                  <div className="text-xs text-muted-foreground mt-1 flex items-center justify-center">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    Скупка
                  </div>
                </CardContent>
              </Card>
              <Card variant="outlined">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-green-500">{lavka.totalSell}</div>
                  <div className="text-xs text-muted-foreground mt-1 flex items-center justify-center">
                    <TrendingDown className="h-3 w-3 mr-1" />
                    Продажа
                  </div>
                </CardContent>
              </Card>
              <Card variant="outlined">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-purple-500">
                    {lavka.totalBuy + lavka.totalSell}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Всего предметов
                  </div>
                </CardContent>
              </Card>
              <Card variant="outlined">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-orange-500">
                    {serverName}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Сервер
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Buy Offers */}
      {lavka.buyItems.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-blue-500" />
            <span>Скупка ({lavka.buyItems.length})</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {lavka.buyItems.map((item, index) => (
              <motion.div
                key={`${item.itemId}-${index}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.03 }}
              >
                <Card>
                  <CardContent className="p-4">
                    <div className="mb-3">
                      <h3 className="font-semibold text-foreground line-clamp-1">{item.itemName}</h3>
                      <p className="text-xs text-muted-foreground">ID: {item.itemId}</p>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-lg font-bold text-blue-500">
                          {serverId && formatPrice(item.price, parseInt(serverId))}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {item.count} шт.
                        </div>
                      </div>
                      <Badge variant="primary">Скупка</Badge>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Sell Offers */}
      {lavka.sellItems.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center space-x-2">
            <TrendingDown className="h-5 w-5 text-green-500" />
            <span>Продажа ({lavka.sellItems.length})</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {lavka.sellItems.map((item, index) => (
              <motion.div
                key={`${item.itemId}-${index}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.03 }}
              >
                <Card>
                  <CardContent className="p-4">
                    <div className="mb-3">
                      <h3 className="font-semibold text-foreground line-clamp-1">{item.itemName}</h3>
                      <p className="text-xs text-muted-foreground">ID: {item.itemId}</p>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-lg font-bold text-green-500">
                          {serverId && formatPrice(item.price, parseInt(serverId))}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {item.count} шт.
                        </div>
                      </div>
                      <Badge variant="success">Продажа</Badge>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {lavka.buyItems.length === 0 && lavka.sellItems.length === 0 && (
        <Card>
          <CardContent>
            <EmptyState
              title="Нет предметов"
              description="В этой лавке пока нет активных предложений"
              icon={<Store className="h-16 w-16" />}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
