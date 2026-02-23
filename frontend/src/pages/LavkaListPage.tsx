import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/marketplace';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { Store, Users, ArrowLeft, ShoppingCart, Tag } from 'lucide-react';
import { LavkaModal } from '../components/LavkaModal';

interface Lavka {
  lavkaUid: string;
  username: string;
  serverId: number;
  sellCount: number;
  buyCount: number;
  totalItems: number;
}

export function LavkaListPage() {
  const { serverId } = useParams<{ serverId: string }>();
  const navigate = useNavigate();
  const [lavkas, setLavkas] = useState<Lavka[]>([]);
  const [serverName, setServerName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLavka, setSelectedLavka] = useState<Lavka | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadLavkas = useCallback(async () => {
    if (!serverId) {
      navigate('/');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<{
        lavkas: Lavka[];
        total: number;
        serverName: string;
      }>(`/marketplace/lavkas?server_id=${serverId}`);

      setLavkas(response.data.lavkas);
      setServerName(response.data.serverName);
    } catch (err) {
      setError('Ошибка загрузки списка лавок');
      console.error('Error loading lavkas:', err);
    } finally {
      setIsLoading(false);
    }
  }, [serverId, navigate]);

  useEffect(() => {
    loadLavkas();
  }, [loadLavkas]);

  const handleOpenLavka = (lavka: Lavka) => {
    setSelectedLavka(lavka);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedLavka(null);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return <ErrorState title="Ошибка" description={error} onRetry={loadLavkas} />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Заголовок */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center text-gray-400 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Назад
        </button>
        <h1 className="text-3xl font-bold text-white mb-2">
          Лавки сервера {serverName}
        </h1>
        <p className="text-gray-400">
          Найдено лавок: <span className="text-white font-medium">{lavkas.length}</span>
        </p>
      </div>

      {/* Список лавок */}
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
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="h-12 w-12 bg-primary-600/20 rounded-lg flex items-center justify-center">
                      <Store className="h-6 w-6 text-primary-500" />
                    </div>
                    <div>
                      <CardTitle className="text-white text-lg">{lavka.username}</CardTitle>
                      <p className="text-sm text-gray-400">ID: {lavka.lavkaUid}</p>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center p-3 bg-blue-600/10 rounded-lg">
                    <div className="flex items-center justify-center mb-1">
                      <ShoppingCart className="h-4 w-4 text-blue-500 mr-1" />
                      <span className="text-xs text-blue-400">Скупка</span>
                    </div>
                    <p className="text-xl font-bold text-blue-500">{lavka.buyCount}</p>
                  </div>
                  <div className="text-center p-3 bg-green-600/10 rounded-lg">
                    <div className="flex items-center justify-center mb-1">
                      <Tag className="h-4 w-4 text-green-500 mr-1" />
                      <span className="text-xs text-green-400">Продажа</span>
                    </div>
                    <p className="text-xl font-bold text-green-500">{lavka.sellCount}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                  <div className="flex items-center">
                    <Users className="h-4 w-4 mr-1" />
                    <span>Всего: {lavka.totalItems}</span>
                  </div>
                </div>

                <Button
                  onClick={() => handleOpenLavka(lavka)}
                  variant="primary"
                  className="w-full"
                >
                  <Store className="h-4 w-4 mr-2" />
                  Открыть лавку
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Модальное окно лавки */}
      {selectedLavka && (
        <LavkaModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          lavkaUid={selectedLavka.lavkaUid}
          username={selectedLavka.username}
          serverId={selectedLavka.serverId}
        />
      )}
    </div>
  );
}
