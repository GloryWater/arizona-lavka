# Arizona Lavka Marketplace - Проект

## Обзор проекта

Arizona Lavka Marketplace - это коммерческий веб-проект, представляющий собой BFF (Backend-For-Frontend) для marketplace Arizona RP (GTA 5 Online). Проект состоит из двух основных компонентов:

1. **Backend**: FastAPI-приложение (Python) с PostgreSQL базой данных
2. **Frontend**: Современное React-приложение (TypeScript, Vite, TailwindCSS)

Проект использует Docker для контейнеризации и включает систему мониторинга (Prometheus + Grafana).

## Архитектура

### Backend (Python/FastAPI)
- **Фреймворк**: FastAPI 0.109.2
- **База данных**: PostgreSQL 17 (асинхронный доступ через asyncpg)
- **ORM**: SQLAlchemy 2.0.25
- **Аутентификация**: JWT-токены, OAuth, Telegram WebApp аутентификация
- **Валидация**: Pydantic 2.6.1
- **Безопасность**: Cloudflare Turnstile (ботозащита), ограничение частоты запросов
- **Мониторинг**: Prometheus клиент для сбора метрик
- **Планировщик задач**: APScheduler для ежедневной очистки неподтвержденных пользователей

### Frontend (React/TypeScript)
- **Фреймворк**: React 19.0.0
- **Язык**: TypeScript
- **Сборка**: Vite 6.0.3
- **Стили**: TailwindCSS
- **HTTP клиент**: Axios
- **Состояние**: Zustand, React Query
- **UI компоненты**: Lucide React, Framer Motion
- **Валидация форм**: Zod + React Hook Form
- **Таблицы**: TanStack Table
- **Графики**: Recharts

## Структура проекта

```
D:\code\python\arizonalavka\
├── .env                          # Файл с переменными окружения
├── docker-compose.yml           # Основная конфигурация Docker Compose
├── docker-compose.secure.yml    # Безопасная конфигурация Docker Compose
├── docker-compose.monitoring.yml # Конфигурация мониторинга
├── SECURITY_SETUP.md            # Документация по безопасности
├── generate_secrets.py          # Скрипт генерации безопасных секретов
├── rules.md                     # Инструкции по настройке nginx
├── index.html                   # Главный HTML шаблон
├── backend/                     # Серверная часть
│   ├── main.py                  # Главный файл приложения
│   ├── config.py                # Конфигурация приложения (обновлена для безопасности)
│   ├── utils/secrets_manager.py # Новый модуль безопасного управления секретами
│   ├── requirements.txt         # Зависимости Python
│   ├── application/             # Бизнес-логика
│   ├── core/                    # Ядро приложения
│   ├── infrastructure/          # Инфраструктурный код (БД, кэш)
│   ├── interfaces/              # Интерфейсы (HTTP, CLI)
│   ├── routes/                  # Роуты API
│   ├── services/                # Бизнес-сервисы
│   ├── utils/                   # Утилиты
│   └── ...
├── frontend/                    # Клиентская часть
│   ├── package.json             # Зависимости Node.js
│   ├── src/                     # Исходный код React
│   ├── dist/                    # Собранные файлы
│   ├── nginx.conf               # Конфигурация nginx для фронтенда
│   └── ...
├── monitoring/                  # Файлы конфигурации мониторинга
└── data/                        # Директория для данных
```

## Запуск и эксплуатация

### Безопасный запуск (рекомендуется)
```bash
# Сгенерировать безопасные секреты
python generate_secrets.py

# Запуск всего стека через безопасную конфигурацию Docker
docker compose -f docker-compose.secure.yml up -d

# Запуск только мониторинга
docker compose -f docker-compose.monitoring.yml up -d
```

### Локальный запуск (для разработки)
```bash
# Запуск всего стека через обычную конфигурацию Docker
docker compose up -d
```

### Порты
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Database**: localhost:7432 (PostgreSQL)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Node Exporter**: http://localhost:9100

### Основные функции
- **Аутентификация**: JWT, OAuth, Telegram WebApp
- **Управление пользователями**: регистрация, верификация по email
- **Marketplace**: работа с товарами и категориями
- **Администрирование**: админ-панель с метриками
- **Безопасность**: защита от ботов, ограничение частоты запросов
- **Мониторинг**: Prometheus метрики, логирование

## Особенности реализации

1. **Безопасность**:
   - Cloudflare Turnstile для защиты от ботов
   - Ограничение количества попыток входа
   - Проверка disposable email доменов
   - IP-блокировка и fingerprinting устройств
   - **НОВОЕ**: Безопасное управление всеми чувствительными данными
   - Защита от SQL-инъекций, XSS и CSRF атак
   - Защита от DDoS-атак с использованием rate limiting

2. **Производительность**:
   - Многоуровневое кэширование (Redis + in-memory)
   - Кэширование на уровне приложения с поддержкой различных стратегий
   - Асинхронная работа с базой данных
   - Connection pooling для оптимизации использования соединений
   - Rate limiting

3. **Мониторинг**:
   - Система сбора метрик Prometheus
   - Логирование всех операций
   - Планировщик задач для очистки данных
   - Метрики производительности кэширования

4. **Интеграции**:
   - Внешнее API (https://api.arz.market/)
   - Telegram Bot API
   - Gmail SMTP для отправки писем верификации

5. **Архитектура**:
   - Четкое разделение на слои (presentation, application, domain, infrastructure)
   - Использование паттернов проектирования (Repository, Unit of Work, Service Layer)
   - Поддержка горизонтального масштабирования

## Технические особенности

- **Версионирование**: API v3.0, Frontend v5.0.0
- **Документация API**: автоматически генерируется через FastAPI (доступна по /docs и /redoc)
- **Конфигурация**: через переменные окружения и безопасное управление секретами
- **Тестирование**: Vitest, Playwright для E2E тестирования
- **CI/CD готовность**: полноценная Docker-контейнеризация

## Домен и SSL
- Основной домен: `lavka.glorysyntax.live`
- SSL сертификаты настраиваются через Let's Encrypt
- Поддержка HTTPS с переадресацией с HTTP

## Система кэширования

Arizona Lavka Marketplace использует многоуровневую систему кэширования для повышения производительности:

- **Redis-кэш**: Основной кэш для хранения данных с возможностью персистентности
- **In-memory кэш**: Быстрый кэш в памяти как резервный вариант
- **Кэширование на уровне приложения**: Интеграция с основными компонентами приложения
- **Декораторы кэширования**: Удобные инструменты для кэширования результатов функций

### Стратегии кэширования:
- **TTL (Time-To-Life)**: Автоматическое удаление данных после истечения времени
- **Sliding expiration**: Продление времени жизни при каждом обращении
- **Write-through**: Обновление кэша при записи в БД
- **Read-through**: Автоматическая загрузка данных в кэш при первом обращении

## Безопасность

Проект включает расширенные меры безопасности для защиты чувствительных данных:

- **Безопасное управление секретами**: Все чувствительные данные (пароли, API ключи, JWT секреты) теперь управляются через безопасную систему, которая поддерживает несколько источников (Docker secrets, зашифрованные файлы, переменные окружения)
- **Защита от хардкода**: Устранены проблемы с хардкодингом чувствительных данных в конфигурационных файлах
- **Шифрование на диске**: Секреты, хранящиеся локально, зашифрованы с использованием Fernet (AES 128)
- **Поддержка Docker secrets**: Полная совместимость с системой секретов Docker для продвинутых конфигураций развёртывания

### Приоритет источников секретов:
1. Зашифрованные файлы в директории `secrets/` (через `SecretsManager`)
2. Docker secret файлы (если указаны переменные *_FILE)
3. Переменные окружения
4. Значения по умолчанию

## Сборка и запуск

Для запуска проекта в режиме разработки:

1. Установите Docker и Docker Compose
2. Сгенерируйте безопасные секреты:
   ```bash
   python generate_secrets.py
   ```
3. Запустите проект:
   ```bash
   docker compose -f docker-compose.secure.yml up -d
   ```

Для локальной разработки можно использовать:
```bash
docker compose up -d
```

## Технологии

### Backend:
- Python 3.11+
- FastAPI
- PostgreSQL 17
- SQLAlchemy 2.0.25
- Redis
- asyncpg
- Pydantic
- APScheduler
- Prometheus client

### Frontend:
- React 19.0.0
- TypeScript
- Vite 6.0.3
- TailwindCSS
- Axios
- Zustand
- React Query
- Lucide React
- Framer Motion
- Zod
- TanStack Table
- Recharts

### Инфраструктура:
- Docker
- Docker Compose
- Nginx
- Prometheus
- Grafana