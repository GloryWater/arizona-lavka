import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/marketplace';
import { Offer, Server, Lavka } from '../types';
import { Card, CardContent } from '../components/ui/Card';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { Search, Store, TrendingUp, TrendingDown, ServerIcon, ArrowUpDown } from 'lucide-react';

interface SearchResults {
  buy_offers: Offer[];
  sell_offers: Offer[];
  total_buy: number;
  total_sell: number;
}

interface LavkasResponse {
  lavkas: Lavka[];
  total: number;
  serverName: string;
}

// Функция для определения валюты сервера
const getServerCurrency = (serverId: number | string): string => {
  const serverIdNum = typeof serverId === 'string' ? parseInt(serverId) : serverId;
  return serverIdNum === 0 ? 'VC$' : 'SA$';
};

export function HomePage() {
  const [servers, setServers] = useState<Server[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedServer, setSelectedServer] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | 'none'>('desc');
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [lavkas, setLavkas] = useState<Lavka[]>([]);
  const [viewMode, setViewMode] = useState<'search' | 'lavkas' | 'empty'>('empty');

  // Загрузка серверов
  useEffect(() => {
    const loadServers = async () => {
      try {
        const response = await apiClient.get<{ servers: Server[] }>('/marketplace/servers');
        setServers(response.data.servers);
      } catch (err) {
        console.error('Error loading servers:', err);
      }
    };
    loadServers();
  }, []);

  // Поиск предметов (от 3 символов)
  const performSearch = useCallback(async () => {
    if (searchTerm.length < 3) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const params: Record<string, string | number> = {
        search_term: searchTerm,
        limit: 100,
        offset: 0,
        sort_order: sortOrder,
      };

      if (selectedServer) {
        params.server_id = parseInt(selectedServer);
      } else {
        params.server_id = -1; // Все серверы
      }

      const response = await apiClient.get<SearchResults>('/marketplace/search', { params });
      setSearchResults(response.data);
      setViewMode('search');
    } catch (err) {
      setError('Ошибка поиска');
      console.error('Error searching:', err);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, selectedServer, sortOrder]);

  // Загрузка лавок сервера
  const loadLavkas = useCallback(async () => {
    if (!selectedServer) {
      setViewMode('empty');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<LavkasResponse>(`/marketplace/lavkas?server_id=${selectedServer}`);
      // Сортируем лавки по lavkaUid
      const sortedLavkas = response.data.lavkas.sort((a, b) => 
        a.lavkaUid.localeCompare(b.lavkaUid)
      );
      setLavkas(sortedLavkas);
      setViewMode('lavkas');
    } catch (err) {
      setError('Ошибка загрузки лавок');
      console.error('Error loading lavkas:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedServer]);

  // Обработка выбора сервера
  const handleServerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const serverId = e.target.value;
    setSelectedServer(serverId);
    
    // Если сервер выбран и нет поиска - показываем лавки
    if (serverId && !searchTerm) {
      loadLavkas();
    } else if (serverId && searchTerm.length >= 3) {
      performSearch();
    }
  };

  // Обработка поиска
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (searchTerm.length >= 3) {
        if (selectedServer) {
          performSearch();
        } else {
          performSearch();
        }
      } else if (searchTerm.length === 0 && selectedServer) {
        loadLavkas();
      } else if (searchTerm.length === 0 && !selectedServer) {
        setViewMode('empty');
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, selectedServer, performSearch, loadLavkas]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  // Получение валюты для текущего сервера
  const currency = selectedServer ? getServerCurrency(parseInt(selectedServer)) : 'VC$';

  // Рендер карточки предложения
  const renderOfferCard = (offer: Offer, index: number) => (
    <Card key={`${offer.lavkaUid}-${offer.itemId}-${index}`} hoverable className="transition-all hover:shadow-lg">
      <CardContent className="p-0">
        <div className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                {offer.type === 'sell' ? (
                  <TrendingDown className="h-4 w-4 text-green-500" />
                ) : (
                  <TrendingUp className="h-4 w-4 text-blue-500" />
                )}
                <span className={`text-sm font-medium ${
                  offer.type === 'sell' ? 'text-green-500' : 'text-blue-500'
                }`}>
                  {offer.type === 'sell' ? 'Продажа' : 'Скупка'}
                </span>
              </div>
              <h3 className="text-white font-medium line-clamp-2">{offer.itemName}</h3>
            </div>
          </div>

          <div className="mb-3">
            <span className="text-2xl font-bold text-primary-500">
              {new Intl.NumberFormat('ru-RU').format(offer.price)} {currency}
            </span>
          </div>

          <div className="space-y-2 text-sm text-gray-400">
            <div className="flex justify-between">
              <span>Количество:</span>
              <span className="text-white">{offer.count} шт.</span>
            </div>
            <div className="flex justify-between">
              <span>Продавец:</span>
              <span className="text-white">{offer.username}</span>
            </div>
            <div className="flex justify-between">
              <span>Сервер:</span>
              <span className="text-white">{offer.serverName}</span>
            </div>
          </div>
        </div>

        <Link
          to={`/lavka/${offer.lavkaUid}`}
          className="block bg-dark-border hover:bg-dark-border/80 text-center py-2 text-sm text-white transition-colors"
        >
          <div className="flex items-center justify-center space-x-1">
            <Store className="h-4 w-4" />
            <span>Перейти в лавку</span>
          </div>
        </Link>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Marketplace</h1>
        <p className="text-gray-400">
          Поиск предложений и лавок по серверам Arizona RP
        </p>
      </div>

      {/* Панель поиска и выбора сервера */}
      <Card className="mb-8">
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                <ServerIcon className="inline h-4 w-4 mr-1" />
                Сервер
              </label>
              <select
                className="select w-full"
                value={selectedServer}
                onChange={handleServerChange}
              >
                <option value="">Выберите сервер</option>
                {servers.map((server) => (
                  <option key={server.id} value={server.id}>
                    {server.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                <Search className="inline h-4 w-4 mr-1" />
                Поиск предмета по названию
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  className="input w-full pl-10"
                  placeholder="От 3 символов..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                <ArrowUpDown className="inline h-4 w-4 mr-1" />
                Сортировка по цене
              </label>
              <select
                className="select w-full"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc' | 'none')}
              >
                <option value="desc">По убыванию ↓</option>
                <option value="asc">По возрастанию ↑</option>
                <option value="none">Без сортировки</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Контент */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      ) : error ? (
        <ErrorState title="Ошибка" description={error} onRetry={() => {
          setError(null);
          if (viewMode === 'lavkas') loadLavkas();
          else if (viewMode === 'search') performSearch();
        }} />
      ) : viewMode === 'empty' ? (
        <EmptyState
          title="Выберите сервер"
          description="Выберите сервер из списка выше, чтобы увидеть лавки, или начните поиск предмета"
          icon={<ServerIcon className="h-12 w-12 text-gray-500" />}
        />
      ) : viewMode === 'lavkas' ? (
        // Отображение лавок
        <div>
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-white">
              Лавки сервера {servers.find(s => s.id.toString() === selectedServer)?.name || 'Unknown'}
            </h2>
            <p className="text-gray-400 text-sm">
              Найдено лавок: {lavkas.length}
            </p>
          </div>

          {lavkas.length === 0 ? (
            <EmptyState
              title="Нет лавок"
              description="На этом сервере пока нет активных лавок"
              icon={<Store className="h-12 w-12 text-gray-500" />}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {lavkas.map((lavka) => (
                <Card key={lavka.lavkaUid} hoverable className="transition-all hover:shadow-lg">
                  <CardContent>
                    <div className="mb-4">
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {lavka.username}
                      </h3>
                      <p className="text-sm text-gray-400 mb-2">
                        ID лавки: {lavka.lavkaUid}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-lg font-bold text-blue-500">{lavka.buyCount}</div>
                        <div className="text-xs text-gray-400">Скупка</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-500">{lavka.sellCount}</div>
                        <div className="text-xs text-gray-400">Продажа</div>
                      </div>
                    </div>

                    <div className="text-sm text-gray-400 mb-4">
                      Всего предметов: <span className="text-white">{lavka.totalItems}</span>
                    </div>

                    <Link
                      to={`/lavka/${lavka.lavkaUid}`}
                      className="block bg-primary-600 hover:bg-primary-700 text-white text-center py-2 rounded-lg transition-colors"
                    >
                      <div className="flex items-center justify-center space-x-1">
                        <Store className="h-4 w-4" />
                        <span>Открыть лавку</span>
                      </div>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : viewMode === 'search' && searchResults ? (
        // Отображение результатов поиска
        <div>
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-white">
              Результаты поиска "{searchTerm}"
            </h2>
            <p className="text-gray-400 text-sm">
              Найдено: скупка {searchResults.total_buy}, продажа {searchResults.total_sell}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Скупка */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-blue-500 flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Скупка (игроки покупают)
                </h3>
                <span className="text-sm text-gray-400">{searchResults.total_buy} предложений</span>
              </div>
              <div className="space-y-4">
                {searchResults.buy_offers.length > 0 ? (
                  searchResults.buy_offers.map((offer, index) => renderOfferCard(offer, index))
                ) : (
                  <div className="text-center py-8 text-gray-400 bg-dark-border rounded-lg">
                    Нет предложений скупки
                  </div>
                )}
              </div>
            </div>

            {/* Продажа */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-green-500 flex items-center">
                  <TrendingDown className="h-5 w-5 mr-2" />
                  Продажа (игроки продают)
                </h3>
                <span className="text-sm text-gray-400">{searchResults.total_sell} предложений</span>
              </div>
              <div className="space-y-4">
                {searchResults.sell_offers.length > 0 ? (
                  searchResults.sell_offers.map((offer, index) => renderOfferCard(offer, index))
                ) : (
                  <div className="text-center py-8 text-gray-400 bg-dark-border rounded-lg">
                    Нет предложений продажи
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
