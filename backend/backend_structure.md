# Arizona Lavka Marketplace - Техническое Функциональное Описание Бэкенда

## Обзор

Arizona Lavka Marketplace - это BFF (Backend-For-Frontend) приложение для marketplace Arizona RP (GTA 5 Online), реализованное на Python с использованием фреймворка FastAPI. Приложение предоставляет API для аутентификации, управления пользователями, работы с marketplace, генерации конфигов и администрирования.

## Архитектура

### Общая структура

Проект следует принципам Clean Architecture и разделен на следующие основные слои:

- **application** - прикладной слой (DTOs, интерфейсы, сервисы)
- **core** - ядро приложения (сущности, перечисления)
- **infrastructure** - инфраструктурный слой (база данных, кэш, внешние API)
- **interfaces** - интерфейсы взаимодействия (HTTP middleware)
- **routes** - маршруты API
- **services** - бизнес-сервисы
- **utils** - утилиты

### Слой Application

Содержит прикладную логику приложения:

- **dtos** - объекты передачи данных
- **interfaces** - интерфейсы для внедрения зависимостей
- **services** - прикладные сервисы

### Слой Core

Содержит бизнес-логику и доменные объекты:

- **entities** - доменные сущности (UserEntity, ConfigHistoryEntity, и т.д.)
- **enums** - перечисления (ConfigMode, OfferType)

### Слой Infrastructure

Содержит реализации инфраструктурных компонентов:

- **cache** - реализация кэширования (Redis, in-memory)
- **database** - ORM модели и подключения к БД
- **external** - интеграции с внешними API
- **persistence** - репозитории и реализации интерфейсов доступа к данным

### Слой Interfaces

Содержит HTTP-интерфейсы:

- **http** - HTTP middleware и обработка запросов

### Папка Routes

Содержит маршруты API:

- **admin_metrics.py** - метрики для администраторов
- **admin.py** - административные функции
- **auth.py** - аутентификация
- **config.py** - генерация конфигов
- **health.py** - проверки работоспособности
- **marketplace.py** - функции marketplace
- **metrics.py** - сбор метрик
- **telegram_auth.py** - аутентификация через Telegram
- **user_management_routes.py** - управление пользователями
- **user.py** - пользовательские функции

### Папка Services

Содержит бизнес-сервисы:

- **audit_log_service.py** - логирование аудита
- **auth_service.py** - сервис аутентификации
- **cleanup_service.py** - очистка данных
- **config_generator_service.py** - генерация конфигов
- **email_verification_service.py** - верификация email
- **historical_data_service.py** - работа с историческими данными
- **item_categories.py** - категории товаров
- **lavka_service.py** - сервис лавки
- **maintenance_service.py** - обслуживание системы
- **marketplace_service.py** - сервис marketplace
- **metrics_service.py** - сбор метрик
- **security_service.py** - безопасность
- **telegram_auth_service.py** - аутентификация через Telegram
- **turnstile_service.py** - защита от ботов

## Основные компоненты

### main.py - точка входа

Основной файл приложения, содержащий:

- Настройку логирования
- Управление жизненным циклом приложения (lifespan)
- Инициализацию базы данных, Redis и кэша
- Настройку middleware
- Регистрацию маршрутов
- Запуск планировщика задач (APScheduler) для ежедневной очистки неподтвержденных пользователей

### config.py - система конфигурации

Система управления конфигурацией с поддержкой:

- Безопасного хранения секретов (через SecretsManager)
- Docker secrets
- Переменных окружения
- Значений по умолчанию

Ключевые настройки:
- Подключение к PostgreSQL
- JWT параметры
- CORS настройки
- Настройки кэширования
- Ограничения частоты запросов
- Параметры безопасности
- Настройки SMTP для отправки email
- Настройки Redis

### models.py - слой совместимости

Файл обеспечивает обратную совместимость, импортируя:
- ORM модели из infrastructure
- Доменные сущности из core
- Pydantic схемы из schemas

### schemas.py - Pydantic схемы

Содержит схемы для валидации запросов и ответов API:
- Схемы marketplace (Offer, LavkaItem, и т.д.)
- Схемы аутентификации (UserRegister, UserLogin, и т.д.)
- Схемы администрирования (AdminUserResponse, AdminLogResponse, и т.д.)
- Схемы метрик (SessionStartRequest, PageViewRequest, и т.д.)

## Безопасность

### Middleware

- **Security middleware** - защита от атак, установка безопасных заголовков
- **Rate limiting** - ограничение частоты запросов
- **Logging middleware** - логирование запросов
- **Maintenance middleware** - режим обслуживания

### Защитные механизмы

- Cloudflare Turnstile для защиты от ботов
- Проверка disposable email доменов
- Ограничение попыток входа
- IP-блокировка
- Device fingerprinting
- Проверка длины паролей

## Кэширование

Система кэширования поддерживает:
- Redis как основной кэш
- In-memory кэш как резервный вариант
- Стратегии TTL (Time-To-Live)
- Сжатие больших значений
- Сериализацию (JSON, pickle, msgpack)
- Метрики производительности кэширования

## Мониторинг

- Сбор метрик через Prometheus
- Логирование всех операций
- Метрики производительности кэширования
- Система аудита действий пользователей

## Планировщик задач

Используется APScheduler для:
- Ежедневной очистки неподтвержденных пользователей
- Других регулярных задач обслуживания

## API Эндпоинты

### Health Check
- `/` - корневой эндпоинт
- `/health` - проверка работоспособности
- `/api/health` - альтернативная проверка

### Аутентификация
- `/api/auth/register` - регистрация
- `/api/auth/login` - вход
- `/api/auth/refresh` - обновление токена
- `/api/auth/logout` - выход
- `/api/auth/verify-email` - подтверждение email
- `/api/auth/resend-verification` - повторная отправка письма верификации

### Пользователи
- `/api/user/profile` - профиль пользователя
- `/api/user/update-profile` - обновление профиля
- `/api/user/change-password` - изменение пароля
- `/api/user/favorites` - избранные товары
- `/api/user/alerts` - уведомления о ценах

### Marketplace
- `/api/marketplace/offers` - предложения
- `/api/marketplace/lavka/{lavka_uid}` - детали лавки
- `/api/marketplace/search` - поиск
- `/api/marketplace/servers` - список серверов

### Генерация конфигов
- `/api/config/generate` - генерация конфига
- `/api/config/history` - история конфигов
- `/api/config/download/{history_id}` - скачивание конфига

### Telegram аутентификация
- `/telegram/auth` - аутентификация через Telegram

### Управление пользователями
- `/api/users/list` - список пользователей
- `/api/users/{user_id}` - детали пользователя
- `/api/users/{user_id}/update-role` - изменение роли
- `/api/users/{user_id}/ban` - бан пользователя

### Администрирование
- `/api/v1/admin/stats` - статистика
- `/api/v1/admin/logs` - логи
- `/api/v1/admin/settings` - глобальные настройки
- `/api/v1/admin/users` - управление пользователями

### Метрики
- `/api/metrics/session/start` - начало сессии
- `/api/metrics/session/end` - завершение сессии
- `/api/metrics/page-view` - просмотр страницы
- `/api/metrics/event` - пользовательское событие
- `/api/metrics/conversion` - конверсия

## Зависимости

Основные зависимости:
- FastAPI - веб-фреймворк
- SQLAlchemy - ORM для работы с БД
- asyncpg - асинхронный драйвер PostgreSQL
- Pydantic - валидация данных
- Redis - система кэширования
- APScheduler - планировщик задач
- Prometheus client - сбор метрик
- PyJWT - работа с JWT токенами