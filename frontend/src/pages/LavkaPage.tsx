import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api/marketplace';
import { LavkaDetail, LavkaItem } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { ErrorState } from '../components/states/ErrorState';
import { ArrowLeft, TrendingUp, TrendingDown, User, MapPin } from 'lucide-react';
import { formatPrice } from '../utils/constants';

export function LavkaPage() {
  const { lavkaUid } = useParams<{ lavkaUid: string }>();
  const [lavka, setLavka] = useState<LavkaDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'sell' | 'buy'>('sell');

  useEffect(() => {
    const loadLavka = async () => {
      if (!lavkaUid) return;

      setIsLoading(true);
      setError(null);

      try {
        const response = await apiClient.get<LavkaDetail>(`/marketplace/lavkas/${lavkaUid}`);
        setLavka(response.data);
      } catch (err) {
        setError('Лавка не найдена или произошла ошибка');
        console.error('Error loading lavka:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadLavka();
  }, [lavkaUid]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error || !lavka) {
    return <ErrorState title="Ошибка" description={error || 'Лавка не найдена'} />;
  }

  const items = activeTab === 'sell' ? lavka.sellItems : lavka.buyItems;
  const typeLabel = activeTab === 'sell' ? 'Продажа' : 'Покупка';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Навигация */}
      <Link to="/" className="inline-flex items-center text-gray-400 hover:text-white mb-6">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Назад к marketplace
      </Link>

      {/* Информация о лавке */}
      <Card className="mb-8">
        <CardContent>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">
                Лавка игрока {lavka.username}
              </h1>
              <div className="flex items-center space-x-4 text-gray-400">
                <div className="flex items-center space-x-1">
                  <MapPin className="h-4 w-4" />
                  <span>{lavka.serverName}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <User className="h-4 w-4" />
                  <span>{lavka.totalSell + lavka.totalBuy} предметов</span>
                </div>
              </div>
            </div>

            <div className="mt-4 md:mt-0 flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">{lavka.totalSell}</div>
                <div className="text-sm text-gray-400">На продажу</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-500">{lavka.totalBuy}</div>
                <div className="text-sm text-gray-400">На покупку</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Табы */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setActiveTab('sell')}
          className={`px-6 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'sell'
              ? 'bg-green-600 text-white'
              : 'bg-dark-card text-gray-400 hover:text-white'
          }`}
        >
          Продажа ({lavka.totalSell})
        </button>
        <button
          onClick={() => setActiveTab('buy')}
          className={`px-6 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'buy'
              ? 'bg-blue-600 text-white'
              : 'bg-dark-card text-gray-400 hover:text-white'
          }`}
        >
          Покупка ({lavka.totalBuy})
        </button>
      </div>

      {/* Список предметов */}
      {items.length === 0 ? (
        <Card>
          <CardContent>
            <p className="text-gray-400 text-center py-8">
              Нет предметов в этой категории
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item, index) => (
            <Card key={`${item.type}-${item.itemId}-${index}`} hoverable>
              <CardContent>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      {item.type === 'sell' ? (
                        <TrendingDown className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                      )}
                      <span className={`text-sm font-medium ${
                        item.type === 'sell' ? 'text-green-500' : 'text-blue-500'
                      }`}>
                        {typeLabel}
                      </span>
                    </div>
                    <h3 className="text-white font-medium line-clamp-2">{item.itemName}</h3>
                  </div>
                </div>

                <div className="mb-3">
                  <span className="text-2xl font-bold text-primary-500">
                    {formatPrice(item.price)} $
                  </span>
                </div>

                <div className="text-sm text-gray-400">
                  Количество: <span className="text-white">{item.count} шт.</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
