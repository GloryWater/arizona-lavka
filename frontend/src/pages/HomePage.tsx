'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Search,
  Store,
  TrendingUp,
  TrendingDown,
  Server as ServerIcon,
  Sparkles,
  DollarSign,
  ArrowUpDown,
  Package,
  User,
  MapPin,
  Filter,
} from 'lucide-react';
import { marketplaceApi } from '@/shared/api';
import type { Offer, Lavka } from '@/shared/types';
import { SERVERS } from '@/shared/lib/constants';
import { formatNumber, formatPrice } from '@/shared/lib/helpers';
import {
  Card,
  CardContent,
  Input,
  Select,
  Badge,
  Skeleton,
  EmptyState,
  Button,
} from '@/shared/ui';

type ViewMode = 'search' | 'lavkas' | 'empty';

interface SearchResults {
  buy_offers: Offer[];
  sell_offers: Offer[];
  total_buy: number;
  total_sell: number;
  limit: number;
  offset: number;
  server_id: number | null;
  search_term: string;
  sort_order: string;
}

export function HomePage() {
  // Состояния
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedServer, setSelectedServer] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | 'none'>('desc');
  const [viewMode, setViewMode] = useState<ViewMode>('empty');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce для поиска
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Определение режима просмотра
  useEffect(() => {
    if (debouncedSearch.trim()) {
      setViewMode('search');
    } else if (selectedServer) {
      setViewMode('lavkas');
    } else {
      setViewMode('empty');
    }
  }, [debouncedSearch, selectedServer]);

  // Загрузка лавок
  const { data: lavkasData, isLoading: lavkasLoading } = useQuery({
    queryKey: ['lavkas', selectedServer],
    queryFn: async () => {
      if (!selectedServer) return null;
      const response = await marketplaceApi.getLavkas(parseInt(selectedServer));
      return response;
    },
    enabled: viewMode === 'lavkas',
    staleTime: 1000 * 60 * 2,
  });

  const lavkas = lavkasData?.lavkas || [];
  const lavkasTotal = lavkasData?.total || 0;

  // Поиск предложений
  const { data: searchResults, isLoading: searchLoading } = useQuery<SearchResults>({
    queryKey: ['search', debouncedSearch, selectedServer, sortOrder],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        search_term: debouncedSearch,
        limit: 100,
        offset: 0,
        sort_order: sortOrder,
      };
      if (selectedServer) {
        params.server_id = parseInt(selectedServer);
      }
      return marketplaceApi.search(params as any);
    },
    enabled: viewMode === 'search',
    staleTime: 1000 * 60 * 1,
  });

  const isLoading = lavkasLoading || searchLoading;

  const getServerName = (id: number | string) => {
    const server = SERVERS.find((s) => s.id.toString() === id.toString());
    return server?.name || 'Неизвестно';
  };

  const handleServerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedServer(e.target.value);
    setSearchTerm(''); // Очищаем поиск при смене сервера
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedServer('');
    setSortOrder('desc');
  };

  // Рендер карточки предложения
  const renderOfferCard = (offer: Offer, index: number) => (
    <motion.div
      key={`${offer.type}-${offer.itemId}-${offer.lavkaUid}-${index}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
    >
      <Card hoverable className="group overflow-hidden">
        <CardContent className="p-0">
          <div className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <Badge variant={offer.type === 'sell' ? 'success' : 'primary'}>
                    {offer.type === 'sell' ? (
                      <>
                        <TrendingDown className="h-3 w-3" />
                        Продажа
                      </>
                    ) : (
                      <>
                        <TrendingUp className="h-3 w-3" />
                        Скупка
                      </>
                    )}
                  </Badge>
                </div>
                <h3 className="text-gray-900 dark:text-white font-medium line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {offer.itemName}
                </h3>
              </div>
            </div>

            <div className="mb-3">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
                {formatPrice(offer.price, offer.serverId)}
              </span>
            </div>

            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Package className="h-3 w-3" />
                  Количество:
                </span>
                <span className="font-medium">{offer.count} шт.</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground flex items-center gap-1">
                  <User className="h-3 w-3" />
                  Продавец:
                </span>
                <span className="font-medium">{offer.username}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  Сервер:
                </span>
                <span className="font-medium">{offer.serverName}</span>
              </div>
            </div>
          </div>

          <Link
            to={`/lavka/${offer.lavkaUid}?server_id=${offer.serverId}`}
            className="block bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-center py-2.5 text-sm font-semibold text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            aria-label={`Перейти в лавку ${offer.username} с предметом ${offer.itemName}`}
          >
            <div className="flex items-center justify-center space-x-2">
              <Store className="h-4 w-4" />
              <span>Перейти в лавку</span>
            </div>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  );

  // Рендер карточки лавки
  const renderLavkaCard = (lavka: Lavka, index: number) => (
    <motion.div
      key={lavka.lavkaUid}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
    >
      <Card hoverable>
        <CardContent className="p-4">
          <div className="mb-3">
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

          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="text-center p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <div className="text-lg font-bold text-blue-500">{lavka.buyCount}</div>
              <div className="text-xs text-muted-foreground mt-0.5 flex items-center justify-center gap-1">
                <TrendingUp className="h-3 w-3" />
                Скупка
              </div>
            </div>
            <div className="text-center p-2.5 rounded-lg bg-green-500/10 border border-green-500/20">
              <div className="text-lg font-bold text-green-500">{lavka.sellCount}</div>
              <div className="text-xs text-muted-foreground mt-0.5 flex items-center justify-center gap-1">
                <TrendingDown className="h-3 w-3" />
                Продажа
              </div>
            </div>
          </div>

          <div className="text-sm text-muted-foreground mb-3 flex items-center justify-between">
            <span>Всего предметов:</span>
            <span className="text-foreground font-semibold">{lavka.totalItems}</span>
          </div>

          <Link
            to={`/lavka/${lavka.lavkaUid}?server_id=${selectedServer}`}
            className="block bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-center py-2 rounded-lg font-semibold transition-all"
          >
            <div className="flex items-center justify-center space-x-2">
              <Store className="h-4 w-4" />
              <span>Открыть лавку</span>
            </div>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  );

  return (
    <div className="container max-w-screen-2xl px-4 md:px-6 py-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 relative overflow-hidden glass-card rounded-2xl p-6 md:p-8"
      >
        <div className="flex items-center space-x-4">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            className="h-14 w-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25"
          >
            <Sparkles className="h-7 w-7 text-white" />
          </motion.div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">Marketplace</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Мониторинг предложений в реальном времени
            </p>
          </div>
        </div>
      </motion.div>

      {/* Панель фильтров */}
      <Card className="mb-8">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Select
                label="Сервер"
                value={selectedServer}
                onChange={handleServerChange}
                icon={<ServerIcon className="h-4 w-4" />}
              >
                <option value="">Все серверы</option>
                {SERVERS.map((server) => (
                  <option key={server.id} value={server.id}>
                    {server.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="md:col-span-2">
              <Input
                label="Поиск предмета"
                placeholder="Введите название предмета..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                icon={<Search className="h-5 w-5" />}
              />
            </div>
            <div>
              <Select
                label="Сортировка"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc' | 'none')}
                icon={<ArrowUpDown className="h-4 w-4" />}
              >
                <option value="none">По умолчанию</option>
                <option value="asc">Цена: возрастание</option>
                <option value="desc">Цена: убывание</option>
              </Select>
            </div>
          </div>
          
          {(searchTerm || selectedServer || sortOrder !== 'desc') && (
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {selectedServer && <span>Сервер: {getServerName(selectedServer)} | </span>}
                  {searchTerm && <span>Поиск: "{searchTerm}" | </span>}
                  {sortOrder !== 'desc' && <span>Сортировка: {sortOrder === 'asc' ? 'возрастание' : 'убывание'}</span>}
                </span>
              </div>
              <Button variant="ghost" size="sm" onClick={handleClearFilters}>
                Сбросить фильтры
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats */}
      <AnimatePresence>
        {viewMode !== 'empty' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          >
            <Card variant="outlined">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-blue-500/10 rounded-xl flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Всего предложений</p>
                    <p className="text-lg font-bold">
                      {viewMode === 'search' && searchResults
                        ? formatNumber(searchResults.total_buy + searchResults.total_sell)
                        : lavkasTotal
                        ? formatNumber(lavkasTotal)
                        : '-'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-green-500/10 rounded-xl flex items-center justify-center">
                    <Store className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Лавок</p>
                    <p className="text-lg font-bold">
                      {lavkasTotal ? formatNumber(lavkasTotal) : '-'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-purple-500/10 rounded-xl flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-purple-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Скупка</p>
                    <p className="text-lg font-bold">
                      {searchResults ? formatNumber(searchResults.total_buy) : '-'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-orange-500/10 rounded-xl flex items-center justify-center">
                    <ServerIcon className="h-5 w-5 text-orange-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Сервер</p>
                    <p className="text-lg font-bold">
                      {selectedServer ? getServerName(selectedServer) : 'Все'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Контент */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      ) : viewMode === 'empty' ? (
        <Card>
          <CardContent className="p-12">
            <EmptyState
              title="Начните поиск"
              description="Введите название предмета для поиска предложений или выберите сервер для просмотра лавок"
              icon={<Search className="h-16 w-16" />}
            />
          </CardContent>
        </Card>
      ) : viewMode === 'lavkas' ? (
        <div>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-foreground flex items-center space-x-3">
                <Store className="h-6 w-6 text-blue-500" />
                <span>Лавки сервера {getServerName(selectedServer)}</span>
              </h2>
              <p className="text-muted-foreground mt-1">
                Найдено лавок:{' '}
                <span className="text-blue-500 font-semibold">{lavkasTotal}</span>
              </p>
            </div>
          </div>

          {lavkas.length === 0 ? (
            <Card>
              <CardContent className="p-12">
                <EmptyState
                  title="Нет лавок"
                  description={`На сервере ${getServerName(selectedServer)} пока нет активных лавок`}
                  icon={<Store className="h-16 w-16" />}
                />
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {lavkas.map((lavka, index) => renderLavkaCard(lavka, index))}
            </div>
          )}
        </div>
      ) : viewMode === 'search' && searchResults ? (
        <div>
          <div className="mb-6">
            <h2 className="text-xl font-bold text-foreground flex items-center space-x-3">
              <Search className="h-6 w-6 text-blue-500" />
              <span>Результаты поиска "{debouncedSearch}"</span>
            </h2>
            <div className="flex items-center space-x-4 mt-2">
              <Badge variant="primary">
                <TrendingUp className="h-3 w-3" />
                Скупка: {formatNumber(searchResults.total_buy)}
              </Badge>
              <Badge variant="success">
                <TrendingDown className="h-3 w-3" />
                Продажа: {formatNumber(searchResults.total_sell)}
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-blue-500 flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Скупка
                </h3>
                <Badge variant="primary">{formatNumber(searchResults.total_buy)} предложений</Badge>
              </div>
              <div className="space-y-4">
                {searchResults.buy_offers.length > 0 ? (
                  searchResults.buy_offers.map((offer, index) => renderOfferCard(offer, index))
                ) : (
                  <Card>
                    <CardContent className="p-8">
                      <p className="text-center text-muted-foreground">Нет предложений скупки</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-green-500 flex items-center">
                  <TrendingDown className="h-5 w-5 mr-2" />
                  Продажа
                </h3>
                <Badge variant="success">{formatNumber(searchResults.total_sell)} предложений</Badge>
              </div>
              <div className="space-y-4">
                {searchResults.sell_offers.length > 0 ? (
                  searchResults.sell_offers.map((offer, index) => renderOfferCard(offer, index))
                ) : (
                  <Card>
                    <CardContent className="p-8">
                      <p className="text-center text-muted-foreground">Нет предложений продажи</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
