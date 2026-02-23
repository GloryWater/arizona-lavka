import React, { useState, useEffect } from 'react';
import apiClient from '../api/marketplace';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { X, Store, ShoppingCart, Tag, TrendingUp, TrendingDown } from 'lucide-react';
import { formatPrice } from '../utils/constants';

interface LavkaItem {
  itemId: number;
  itemName: string;
  price: number;
  count: number;
  type: 'buy' | 'sell';
}

interface LavkaDetail {
  lavkaUid: string;
  username: string;
  serverId: number;
  userStatus: boolean;
  sellItems: LavkaItem[];
  buyItems: LavkaItem[];
  totalSell: number;
  totalBuy: number;
}

interface LavkaModalProps {
  isOpen: boolean;
  onClose: () => void;
  lavkaUid: string;
  username: string;
  serverId: number;
}

export function LavkaModal({ isOpen, onClose, lavkaUid, username, serverId }: LavkaModalProps) {
  const [lavka, setLavka] = useState<LavkaDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'buy' | 'sell'>('all');

  useEffect(() => {
    if (isOpen && lavkaUid) {
      loadLavkaDetail();
    }
  }, [isOpen, lavkaUid]);

  const loadLavkaDetail = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<LavkaDetail>(`/marketplace/lavkas/${lavkaUid}`);
      setLavka(response.data);
    } catch (err) {
      setError('Ошибка загрузки информации о лавке');
      console.error('Error loading lavka detail:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setLavka(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-dark-card rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Заголовок */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 bg-primary-600/20 rounded-lg flex items-center justify-center">
              <Store className="h-6 w-6 text-primary-500" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{username}</h2>
              <p className="text-sm text-gray-400">Лавка ID: {lavkaUid}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Контент */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-400">
              <p>{error}</p>
              <Button onClick={loadLavkaDetail} variant="primary" className="mt-4">
                Повторить
              </Button>
            </div>
          ) : lavka ? (
            <>
              {/* Табы */}
              <div className="mb-6">
                <div className="flex space-x-2 border-b border-dark-border">
                  <button
                    onClick={() => setActiveTab('all')}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${
                      activeTab === 'all'
                        ? 'text-primary-500 border-b-2 border-primary-500'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Все ({lavka.totalBuy + lavka.totalSell})
                  </button>
                  <button
                    onClick={() => setActiveTab('buy')}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${
                      activeTab === 'buy'
                        ? 'text-blue-500 border-b-2 border-blue-500'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center space-x-1">
                      <ShoppingCart className="h-4 w-4" />
                      <span>Скупка</span>
                    </div>
                  </button>
                  <button
                    onClick={() => setActiveTab('sell')}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${
                      activeTab === 'sell'
                        ? 'text-green-500 border-b-2 border-green-500'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center space-x-1">
                      <Tag className="h-4 w-4" />
                      <span>Продажа</span>
                    </div>
                  </button>
                </div>
              </div>

              {/* Двухколоночный layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Столбец скупки (BUY) - слева */}
                {(activeTab === 'all' || activeTab === 'buy') && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-blue-500 flex items-center">
                        <ShoppingCart className="h-5 w-5 mr-2" />
                        Скупка (лавка покупает)
                      </h3>
                      <span className="text-sm text-gray-400">{lavka.totalBuy} предметов</span>
                    </div>
                    <div className="space-y-3">
                      {lavka.buyItems.length > 0 ? (
                        lavka.buyItems.map((item, index) => (
                          <Card key={`buy-${item.itemId}-${index}`}>
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <TrendingUp className="h-4 w-4 text-blue-500" />
                                    <span className="text-xs text-blue-400">Покупка</span>
                                  </div>
                                  <h4 className="text-white font-medium">{item.itemName}</h4>
                                </div>
                                <div className="text-right">
                                  <p className="text-xl font-bold text-blue-500">
                                    {formatPrice(item.price)} $
                                  </p>
                                  <p className="text-sm text-gray-400">{item.count} шт.</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))
                      ) : (
                        <div className="text-center py-8 text-gray-400 bg-dark-border rounded-lg">
                          Нет предметов на скупку
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Столбец продажи (SELL) - справа */}
                {(activeTab === 'all' || activeTab === 'sell') && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-green-500 flex items-center">
                        <Tag className="h-5 w-5 mr-2" />
                        Продажа (лавка продает)
                      </h3>
                      <span className="text-sm text-gray-400">{lavka.totalSell} предметов</span>
                    </div>
                    <div className="space-y-3">
                      {lavka.sellItems.length > 0 ? (
                        lavka.sellItems.map((item, index) => (
                          <Card key={`sell-${item.itemId}-${index}`}>
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <TrendingDown className="h-4 w-4 text-green-500" />
                                    <span className="text-xs text-green-400">Продажа</span>
                                  </div>
                                  <h4 className="text-white font-medium">{item.itemName}</h4>
                                </div>
                                <div className="text-right">
                                  <p className="text-xl font-bold text-green-500">
                                    {formatPrice(item.price)} $
                                  </p>
                                  <p className="text-sm text-gray-400">{item.count} шт.</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))
                      ) : (
                        <div className="text-center py-8 text-gray-400 bg-dark-border rounded-lg">
                          Нет предметов на продажу
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
