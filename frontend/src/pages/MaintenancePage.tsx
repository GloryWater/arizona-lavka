'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Clock, RefreshCw } from 'lucide-react';
import { Button } from '@/shared/ui';

export function MaintenancePage() {
  const [countdown, setCountdown] = useState(30);
  const [message, setMessage] = useState('Технические работы. Скоро вернёмся!');
  const [estimatedEnd, setEstimatedEnd] = useState<string | null>(null);

  useEffect(() => {
    // Проверяем статус maintenance при загрузке
    checkMaintenanceStatus();

    // Таймер обратного отсчёта
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          checkMaintenanceStatus();
          return 30;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const checkMaintenanceStatus = async () => {
    try {
      const response = await fetch('/api/v1/admin/maintenance/status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (!data.enabled) {
          // Режим обслуживания выключен, перезагружаем страницу
          window.location.reload();
        }
        if (data.info) {
          setMessage(data.info.message || 'Технические работы');
          setEstimatedEnd(data.info.estimated_end || null);
        }
      }
    } catch (error) {
      console.error('Error checking maintenance status:', error);
    }
  };

  const handleManualRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center px-4 max-w-2xl"
      >
        {/* Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="mx-auto mb-8 h-24 w-24 bg-gradient-to-br from-orange-500 to-red-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-orange-500/25"
        >
          <AlertTriangle className="h-12 w-12 text-white" />
        </motion.div>

        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
          Технические работы
        </h1>

        {/* Message */}
        <p className="text-lg text-zinc-400 mb-8 leading-relaxed">
          {message}
        </p>

        {/* Estimated end */}
        {estimatedEnd && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex items-center justify-center gap-2 text-zinc-500 mb-8"
          >
            <Clock className="h-5 w-5" />
            <span>
              Ожидаемое окончание:{' '}
              {new Date(estimatedEnd).toLocaleString('ru-RU', {
                day: 'numeric',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </motion.div>
        )}

        {/* Auto-refresh indicator */}
        <div className="flex items-center justify-center gap-2 text-zinc-600 mb-8">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <RefreshCw className="h-4 w-4" />
          </motion.div>
          <span className="text-sm">
            Автоматическое обновление через {countdown} сек
          </span>
        </div>

        {/* Manual refresh button */}
        <Button
          variant="outline"
          onClick={handleManualRefresh}
          icon={<RefreshCw className="h-4 w-4" />}
        >
          Обновить страницу
        </Button>

        {/* Footer */}
        <p className="mt-12 text-sm text-zinc-600">
          Приносим извинения за неудобства
        </p>
      </motion.div>
    </div>
  );
}
