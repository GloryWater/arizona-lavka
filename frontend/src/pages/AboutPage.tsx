'use client';

import { motion } from 'framer-motion';
import {
  Info,
  Zap,
  Shield,
  Globe,
  Heart,
  Github,
  ExternalLink,
  Users,
  TrendingUp,
  Clock,
} from 'lucide-react';
import { Card, CardContent } from '@/shared/ui';

const features = [
  {
    icon: <Zap className="h-6 w-6" />,
    title: 'Мгновенный поиск',
    description: 'Поиск предметов по всем серверам в реальном времени с минимальной задержкой',
  },
  {
    icon: <Shield className="h-6 w-6" />,
    title: 'Безопасность',
    description: 'Надёжная аутентификация и защита данных пользователей',
  },
  {
    icon: <Globe className="h-6 w-6" />,
    title: '33 сервера',
    description: 'Поддержка всех серверов Arizona RP в одном месте',
  },
  {
    icon: <Users className="h-6 w-6" />,
    title: 'Удобный интерфейс',
    description: 'Адаптивный дизайн для комфортной работы с любого устройства',
  },
  {
    icon: <TrendingUp className="h-6 w-6" />,
    title: 'Аналитика',
    description: 'Статистика и аналитика торговых предложений',
  },
  {
    icon: <Clock className="h-6 w-6" />,
    title: 'Актуальные данные',
    description: 'Обновление информации в реальном времени',
  },
];

const stats = [
  { label: 'Серверов', value: '33' },
  { label: 'Пользователей', value: '1000+' },
  { label: 'Предметов', value: '500+' },
  { label: 'Лавок', value: '10000+' },
];

export function AboutPage() {
  return (
    <div className="container max-w-screen-3xl px-4 md:px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25 mb-4"
          >
            <Info className="h-8 w-8 text-white" />
          </motion.div>
          <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            О проекте Arizona Lavka
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Современная платформа для мониторинга и автоматизации торговли
            на серверах Arizona RP
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card variant="elevated">
                <CardContent className="p-6 text-center">
                  <div className="text-3xl font-bold text-blue-500 mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {stat.label}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Features */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-foreground text-center mb-8">
            Возможности
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card variant="outlined" className="h-full">
                  <CardContent className="p-6">
                    <div className="h-12 w-12 bg-blue-500/10 rounded-xl flex items-center justify-center mb-4">
                      <div className="text-blue-500">{feature.icon}</div>
                    </div>
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Info Card */}
        <Card className="mb-12">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-foreground mb-4">
              Что такое Arizona Lavka?
            </h2>
            <div className="space-y-4 text-muted-foreground">
              <p>
                <strong className="text-foreground">Arizona Lavka Marketplace</strong> — это
                современная платформа для мониторинга торговых предложений на серверах
                Arizona RP. Мы предоставляем удобный интерфейс для поиска предметов,
                просмотра лавок других игроков и автоматизации торговли.
              </p>
              <p>
                Наш сервис позволяет быстро находить выгодные предложения, сравнивать
                цены на разных серверах и автоматически генерировать конфиги для
                торговых автоматов.
              </p>
              <p>
                Проект разрабатывается с любовью к сообществу Arizona RP и постоянно
                развивается благодаря обратной связи от пользователей.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* CTA */}
        <Card className="mb-12">
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold text-foreground mb-4">
              Присоединяйтесь к нам
            </h2>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              Создайте аккаунт и получите доступ ко всем возможностям платформы
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="/register"
                className="inline-flex items-center justify-center px-6 py-3 text-base font-medium text-white bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-lg shadow-lg shadow-blue-500/25 transition-all"
              >
                Зарегистрироваться
              </a>
              <a
                href="https://github.com/arizonalavka"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-6 py-3 text-base font-medium text-foreground bg-muted hover:bg-muted/80 rounded-lg transition-all"
              >
                <Github className="h-5 w-5 mr-2" />
                GitHub
                <ExternalLink className="h-4 w-4 ml-2" />
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground">
          <p className="flex items-center justify-center gap-1">
            Сделано с <Heart className="h-4 w-4 text-red-500 fill-red-500" /> для
            сообщества Arizona RP
          </p>
          <p className="mt-2">
            © {new Date().getFullYear()} Arizona Lavka Marketplace. Все права защищены.
          </p>
        </div>
      </motion.div>
    </div>
  );
}
