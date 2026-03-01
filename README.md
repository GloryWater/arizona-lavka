# 🏪 Arizona Lavka Marketplace

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat)](LICENSE)

**Arizona Lavka Marketplace** — это полнофункциональная платформа для торговли внутриигровыми предметами на серверах Arizona RP (GTA 5 Online). Система предоставляет удобный интерфейс для просмотра лавок игроков, анализа рыночных цен и генерации оптимальных торговых конфигов.

---

## 📋 Содержание

- [Обзор проекта](#-обзор-проекта)
- [Возможности](#-возможности)
- [Технологический стек](#-технологический-стек)
- [Архитектура](#-архитектура)
- [Требования](#-требования)
- [Быстрый старт (Docker)](#-быстрый-старт-docker)
- [Локальная разработка](#-локальная-разработка)
- [Управление базой данных](#-управление-базой-данных)
- [Нагрузочное тестирование](#-нагрузочное-тестирование)
- [Деплой](#-деплой)
- [Pre-commit Hooks](#-pre-commit-hooks)
- [CI/CD](#-cicd)
- [Troubleshooting](#-troubleshooting)
- [Структура проекта](#-структура-проекта)

---

## 🎯 Обзор проекта

Arizona Lavka Marketplace — это BFF (Backend-For-Frontend) решение, которое агрегирует данные с внешнего API Arizona RP marketplace, предоставляет расширенную аналитику и инструменты для автоматизации торговли.

**Основные пользователи:**
- 🛒 **Игроки Arizona RP** — просмотр лавок, поиск предметов, анализ цен
- ⚙️ **Трейдеры** — генерация торговых конфигов с учётом исторических данных
- 🛡️ **Администраторы** — мониторинг, управление пользователями, аналитика

---

## ✨ Возможности

### Для пользователей
- 📦 **Просмотр лавок** — каталог лавок всех серверов с фильтрацией
- 🔍 **Поиск предметов** — быстрый поиск по названию и категории
- 📊 **Аналитика цен** — текущие и исторические данные о ценах
- ⚡ **Генерация конфигов** — автоматическое создание торговых конфигов с IQR фильтрацией
- 🔐 **Telegram авторизация** — быстрый вход через Telegram
- 📱 **Адаптивный UI** — поддержка мобильных устройств

### Для администраторов
- 👥 **Управление пользователями** — просмотр, блокировка, удаление
- 📈 **Статистика и метрики** — DAU/MAU, конверсия, активность
- 📝 **Аудит логов** — полное логирование действий
- ⚙️ **Глобальные настройки** — управление конфигурацией системы
- 🔧 **Режим обслуживания** — включение maintenance mode

### Технические возможности
- 🚀 **Высокая производительность** — кэширование, circuit breaker, rate limiting
- 📊 **Анализ ликвидности** — 5-факторная модель расчёта ликвидности предметов
- 🛡️ **Детекция манипуляций** — выявление подозрительных паттернов торговли
- 🔄 **Circuit breaker** — защита от cascade failure внешних API
- 📝 **IQR фильтрация** — отсечение выбросов при расчёте цен

---

## 🛠️ Технологический стек

### Backend
| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.12 | Язык программирования |
| **FastAPI** | 0.109 | Web фреймворк |
| **SQLAlchemy** | 2.0 | ORM |
| **AsyncPG** | 0.29 | Асинхронный PostgreSQL драйвер |
| **Alembic** | 1.13 | Миграции БД |
| **Pydantic** | 2.6 | Валидация данных |
| **PyJWT** | 2.8 | JWT токены |
| **Bcrypt** | 4.1 | Хеширование паролей |
| **Httpx** | 0.26 | HTTP клиент |
| **Cachetools** | 5.3 | Кэширование |

### Frontend
| Технология | Версия | Назначение |
|------------|--------|------------|
| **React** | 19.0 | UI библиотека |
| **TypeScript** | 5.7 | Типизация |
| **Vite** | 6.0 | Сборщик |
| **Tailwind CSS** | 3.4 | Стилизация |
| **React Query** | 5.62 | Управление серверным состоянием |
| **Zustand** | 5.0 | State management |
| **React Router** | 7.0 | Роутинг |
| **Axios** | 1.7 | HTTP клиент |
| **Zod** | 3.24 | Валидация схем |
| **Recharts** | 3.7 | Графики и диаграммы |

### Инфраструктура
| Технология | Версия | Назначение |
|------------|--------|------------|
| **PostgreSQL** | 17 | Основная БД |
| **Docker** | Latest | Контейнеризация |
| **Docker Compose** | Latest | Оркестрация |
| **Nginx** | Alpine | Frontend сервер / Reverse proxy |
| **Locust** | 2.43 | Нагрузочное тестирование |
| **k6** | Latest | Нагрузочное тестирование |

---

## 🏗️ Архитектура

### Backend: Clean Architecture / DDD

Backend следует принципам Clean Architecture с разделением на слои:

```
┌─────────────────────────────────────────────────────────┐
│                    Routes (API Layer)                    │
│  - HTTP endpoints                                        │
│  - Request/Response validation                          │
│  - Authentication decorators                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│               Interfaces (Adapters Layer)                │
│  - HTTP Middleware (CORS, Rate Limiting, Logging)       │
│  - External API clients                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                Application (Use Cases)                   │
│  - Business logic orchestration                         │
│  - Transaction management                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Domain (Core)                          │
│  - Enterprise business rules                            │
│  - Domain entities and value objects                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Infrastructure (Implementation)             │
│  - Database repositories                                │
│  - External service implementations                     │
│  - File system operations                               │
└─────────────────────────────────────────────────────────┘
```

#### Слои Backend

| Директория | Назначение | Примеры |
|------------|------------|---------|
| `core/` | Базовые утилиты, константы, общие исключения | `exceptions.py`, `constants.py` |
| `application/` | Бизнес-логика, use cases | `use_cases/`, `commands/`, `queries/` |
| `domain/` | Domain entities, value objects | `entities/`, `value_objects/` |
| `infrastructure/` | Реализация портов (БД, внешние API) | `database/`, `repositories/`, `external_api/` |
| `interfaces/` | Адаптеры (HTTP middleware, clients) | `http/`, `middleware/`, `dto/` |
| `routes/` | API endpoints (controllers) | `auth.py`, `marketplace.py`, `admin.py` |
| `services/` | Сервисы с бизнес-логикой | `auth_service.py`, `config_generator.py` |

### Frontend: Feature-Sliced Design (FSD)

```
src/
├── app/              # Инициализация приложения, провайдеры
├── pages/            # Страницы (роуты)
├── widgets/          # Композитные блоки (header, footer, layout)
├── features/         # Бизнес-фичи (auth, search, theme)
├── entities/         # Бизнес-сущности (user, lavka, offer)
├── shared/           # Переиспользуемый код (UI, hooks, lib, api)
└── types/            # TypeScript типы
```

---

## 📦 Требования

### Обязательные
- **Docker** ≥ 24.0
- **Docker Compose** ≥ 2.20
- **Node.js** ≥ 20.x (для локальной разработки frontend)
- **Python** ≥ 3.12 (для локальной разработки backend)
- **uv** ≥ 0.5 (Python package manager)

### Опциональные
- **PostgreSQL** ≥ 17 (локальная БД, если не через Docker)
- **Locust** (для нагрузочных тестов)
- **k6** (для нагрузочных тестов)

### Проверка установленных зависимостей

```bash
# Docker
docker --version
docker-compose --version

# Node.js
node --version
npm --version

# Python
python --version
uv --version
```

---

## ⚙️ Быстрый старт (Docker)

### 1. Клонируйте репозиторий

```bash
git clone <repository-url> arizonalavka
cd arizonalavka
```

### 2. Настройте переменные окружения

```bash
# Скопируйте шаблоны .env файлов
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

**Обязательно измените в `.env`:**

```bash
# Сгенерируйте безопасные ключи (минимум 32 символа)
JWT_SECRET_KEY=your-super-secret-key-min-32-characters-long-random-string
POSTGRES_PASSWORD=your-super-secure-database-password-change-this

# Обновите CORS для вашего домена
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### 3. Запустите все сервисы

```bash
# Сборка и запуск
docker-compose up --build -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### 4. Проверьте работу

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:8080 | React приложение |
| **Backend API** | http://localhost:8000 | FastAPI API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **PostgreSQL** | localhost:5432 | База данных |

```bash
# Health check
curl http://localhost:8000/health
```

### 5. Остановка сервисов

```bash
# Остановка
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

---

## 💻 Локальная разработка

### Backend

#### 1. Установка зависимостей

```bash
cd backend

# Через uv (рекомендуется)
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
uv pip install -r requirements.txt

# Или через pip
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### 2. Настройка окружения

```bash
# Скопируйте .env.example
cp .env.example .env

# Отредактируйте .env с вашими значениями
# Обязательно: DATABASE_URL, JWT_SECRET_KEY
```

#### 3. Запуск сервера разработки

```bash
# Development mode с auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 4. Применение миграций

```bash
cd backend

# Создать новую миграцию
alembic revision --autogenerate -m "Description of changes"

# Применить все миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Проверить статус миграций
alembic current
```

### Frontend

#### 1. Установка зависимостей

```bash
cd frontend

# Установка зависимостей
npm install

# Или через yarn
yarn install
```

#### 2. Настройка окружения

```bash
# Скопируйте .env.example
cp .env.example .env.local

# Отредактируйте API URL если нужно
VITE_API_URL=http://localhost:8000/api
```

#### 3. Запуск сервера разработки

```bash
# Development mode с hot reload
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Linting
npm run lint
```

#### 4. Очистка кэша

```bash
# Очистка node_modules и dist
npm run clean

# Или вручную
rm -rf node_modules dist
```

---

## 🗄️ Управление базой данных

### Alembic миграции

#### Создание новой миграции

```bash
cd backend

# Автоматическая генерация на основе моделей
alembic revision --autogenerate -m "add_user_table"

# Ручное создание пустой миграции
alembic revision -m "add_indexes_to_orders"
```

#### Применение миграций

```bash
# Применить все миграции
alembic upgrade head

# Применить до конкретной ревизии
alembic upgrade <revision_id>

# Откатить на одну миграцию
alembic downgrade -1

# Откатить до конкретной ревизии
alembic downgrade <revision_id>

# Откатить все миграции
alembic downgrade base
```

#### Полезные команды

```bash
# Текущая ревизия
alembic current

# История миграций
alembic history

# Показать SQL для миграции
alembic upgrade head --sql

# Проверить наличие незакоммиченных изменений
alembic check
```

### Подключение к PostgreSQL

```bash
# Через Docker
docker exec -it arizonalavka-postgres psql -U arizonalavka -d arizonalavka

# Локально (если установлен psql)
psql -h localhost -U arizonalavka -d arizonalavka
```

---

## 📊 Нагрузочное тестирование

### Locust

#### Установка

```bash
cd load_tests

# Через uv
uv pip install -r requirements.txt

# Или через pip
pip install -r requirements.txt
```

#### Запуск веб-интерфейса

```bash
# Запуск с веб-интерфейсом
locust -f locustfile.py --host http://localhost:8000

# Открыть в браузере: http://localhost:8089
```

#### Запуск в headless режиме

```bash
# 100 пользователей, 10 в секунду, 5 минут
locust -f locustfile.py \
    --host http://localhost:8000 \
    --headless \
    -u 100 \
    -r 10 \
    -t 300s \
    --csv results/test_
```

#### Сценарии тестирования

| Сценарий | Команда | Пользователей | Длительность |
|----------|---------|---------------|--------------|
| **Базовый** | `-u 20 -r 2 -t 120s` | 20 | 2 мин |
| **Средний** | `-u 50 -r 5 -t 180s` | 50 | 3 мин |
| **Высокий** | `-u 100 -r 10 -t 300s` | 100 | 5 мин |
| **Стресс** | `-u 500 -r 50 -t 300s` | 500 | 5 мин |

### k6

#### Установка

```bash
# macOS
brew install k6

# Linux
sudo apt-get install k6

# Windows (Chocolatey)
choco install k6
```

#### Запуск тестов

```bash
# Базовый запуск
k6 run load_tests/k6_test.js

# С параметрами
k6 run --vus 100 --duration 3m load_tests/k6_test.js

# С пороговыми значениями
k6 run --thresholds 'http_req_duration<2000' load_tests/k6_test.js
```

#### Анализ результатов

```bash
# Запуск с выводом в JSON
k6 run --out json=results/k6_results.json load_tests/k6_test.js

# Анализ через Python скрипт
python load_tests/analyze_results.py
```

---

## 🚀 Деплой

### Подготовка к деплою

#### 1. Очистка проекта

```bash
# Linux/Mac
chmod +x scripts/clean_before_deploy.sh
./scripts/clean_before_deploy.sh

# Windows (PowerShell)
.\scripts\clean_before_deploy.ps1
```

**Что удаляется:**
- `__pycache__/`, `*.pyc`
- `frontend/node_modules/`, `frontend/dist/`
- `load_tests/results/`
- `*.log`
- `.env.local`, `.env.*.local`

#### 2. Проверка переменных окружения

```bash
# Убедитесь, что все секреты установлены
echo $JWT_SECRET_KEY
echo $POSTGRES_PASSWORD
echo $CORS_ORIGINS
```

#### 3. Сборка образов

```bash
# Пересборка без кэша
docker-compose build --no-cache

# Проверка образов
docker-compose images
```

### Развёртывание на сервере

#### 1. Копирование файлов

```bash
# Копирование на сервер
scp -r . user@server:/opt/arizonalavka

# Или через rsync
rsync -avz --exclude '.git' --exclude '.venv' --exclude 'node_modules' . user@server:/opt/arizonalavka
```

#### 2. Настройка на сервере

```bash
ssh user@server
cd /opt/arizonalavka

# Создание .env из .env.example
cp .env.example .env
nano .env  # Отредактируйте значения
```

#### 3. Запуск сервисов

```bash
# Запуск
docker-compose up -d

# Проверка
docker-compose ps
docker-compose logs -f
```

#### 4. Настройка Nginx (опционально)

```nginx
# /etc/nginx/sites-available/arizonalavka
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔧 Troubleshooting

### Порт уже занят

**Ошибка:** `Address already in use` для портов 8000, 8080, 5432

**Решение:**

```bash
# Найти процесс на порту
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Убить процесс
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Или изменить порт в docker-compose.yml
```

### Ошибка подключения к БД

**Ошибка:** `could not connect to server: Connection refused`

**Решение:**

```bash
# Проверить статус PostgreSQL
docker-compose ps postgres

# Проверить логи
docker-compose logs postgres

# Убедиться, что POSTGRES_HOST=postgres в backend/.env
# Для Docker сети используется имя сервиса, не localhost
```

### Frontend не видит API

**Ошибка:** `Network Error` или `502 Bad Gateway`

**Решение:**

```bash
# Проверить, что backend запущен
docker-compose ps backend

# Проверить CORS настройки в .env
CORS_ORIGINS=http://localhost:8080,http://localhost:3000

# Проверить nginx.conf для правильного proxy_pass
```

### Миграции не применяются

**Ошибка:** `alembic.util.exc.CommandError: Target database is not up to date`

**Решение:**

```bash
# Проверить текущую ревизию
alembic current

# Проверить историю
alembic history

# Применить миграции вручную
alembic upgrade head

# Если есть конфликты, создать новую миграцию
alembic revision --autogenerate -m "fix_schema"
```

### Rate limiting блокирует запросы

**Ошибка:** `429 Too Many Requests`

**Решение:**

```bash
# Увеличить лимит в .env
RATE_LIMIT_PER_MINUTE=200

# Или добавить IP в whitelist
LOAD_TESTING_IPS=127.0.0.1,192.168.1.100

# Перезапустить backend
docker-compose restart backend
```

### JWT токен не валиден

**Ошибка:** `401 Unauthorized: Invalid token`

**Решение:**

```bash
# Проверить JWT_SECRET_KEY в .env
# Убедиться, что ключ одинаковый для backend и frontend
# Ключ должен быть минимум 32 символа

# Перегенерировать ключ
openssl rand -hex 32

# Перезапустить сервисы
docker-compose restart backend
```

### Frontend сборка падает

**Ошибка:** `Module not found` или `TypeScript error`

**Решение:**

```bash
cd frontend

# Очистить кэш
rm -rf node_modules dist package-lock.json

# Переустановить зависимости
npm install

# Проверить TypeScript
npx tsc --noEmit

# Собрать заново
npm run build
```

---

## 📁 Структура проекта

```
arizonalavka/
├── .env.example              # Шаблон переменных окружения
├── .gitignore                # Git ignore правила
├── docker-compose.yml        # Docker оркестрация
├── pyproject.toml            # Python проект и зависимости
├── uv.lock                   # Python lock файл (uv)
│
├── backend/                  # FastAPI backend
│   ├── Dockerfile            # Docker образ backend
│   ├── requirements.txt      # Python зависимости
│   ├── .dockerignore         # Docker ignore для backend
│   ├── .env.example          # Шаблон переменных backend
│   ├── main.py               # Точка входа FastAPI
│   ├── config.py             # Конфигурация приложения
│   ├── database.py           # DB сессии и зависимости
│   ├── models.py             # Pydantic модели
│   ├── items.json            # Mapping предметов ID→Название
│   ├── alembic/              # Alembic миграции
│   │   ├── versions/         # Файлы миграций
│   │   └── env.py            # Alembic окружение
│   ├── alembic.ini           # Alembic конфигурация
│   ├── application/          # Бизнес-логика (Use Cases)
│   ├── infrastructure/       # Инфраструктурный слой
│   │   ├── database/         # DB модели и репозитории
│   │   └── persistence/      # Кэширование, rate limiting
│   ├── interfaces/           # HTTP адаптеры
│   │   └── http/             # Middleware
│   ├── routes/               # API endpoints
│   │   ├── auth.py           # Аутентификация
│   │   ├── marketplace.py    # Marketplace API
│   │   ├── config.py         # Config generator API
│   │   └── admin.py          # Admin panel API
│   ├── services/             # Сервисы с бизнес-логикой
│   │   ├── auth_service.py
│   │   ├── marketplace_service.py
│   │   ├── config_generator_service.py
│   │   └── historical_data_service.py
│   └── core/                 # Утилиты и константы
│
├── frontend/                 # React frontend
│   ├── Dockerfile            # Docker образ frontend
│   ├── nginx.conf            # Nginx конфигурация
│   ├── package.json          # Node.js зависимости
│   ├── .dockerignore         # Docker ignore для frontend
│   ├── .env.example          # Шаблон переменных frontend
│   ├── index.html            # HTML шаблон
│   ├── src/                  # Исходный код
│   │   ├── app/              # Инициализация приложения
│   │   ├── pages/            # Страницы
│   │   ├── widgets/          # Виджеты
│   │   ├── features/         # Фичи
│   │   ├── entities/         # Сущности
│   │   ├── shared/           # Общий код
│   │   └── types/            # TypeScript типы
│   ├── vite.config.ts        # Vite конфигурация
│   ├── tailwind.config.js    # Tailwind конфигурация
│   ├── tsconfig.json         # TypeScript конфигурация
│   └── postcss.config.js     # PostCSS конфигурация
│
├── data/                     # Исторические данные marketplace
│   ├── info_users_buy_{server}.json
│   └── info_users_sell_{server}.json
│
├── load_tests/               # Нагрузочное тестирование
│   ├── locustfile.py         # Locust сценарии
│   ├── k6_test.js            # k6 сценарии
│   ├── analyze_results.py    # Скрипт анализа результатов
│   ├── requirements.txt      # Python зависимости для тестов
│   └── run_tests.sh          # Bash скрипт запуска
│
└── scripts/                  # Скрипты для деплоя
    ├── clean_before_deploy.sh    # Bash версия очистки
    └── clean_before_deploy.ps1   # PowerShell версия очистки
```

---

## 🔧 Pre-commit Hooks

Проект использует pre-commit hooks для автоматической проверки кода перед коммитом.

### Установка

```bash
# Linux/Mac
chmod +x scripts/install-pre-commit.sh
./scripts/install-pre-commit.sh

# Windows (PowerShell)
.\scripts\install-pre-commit.ps1

# Или вручную
pip install pre-commit
pre-commit install
```

### Запуск вручную

```bash
# Запуск всех проверок
pre-commit run --all-files

# Запуск конкретной проверки
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

### Доступные хуки

| Хук | Описание |
|-----|----------|
| **Ruff lint** | Проверка кода на ошибки и стиль |
| **Ruff format** | Форматирование кода |
| **MyPy** | Проверка типов |
| **Bandit** | Проверка безопасности |
| **ESLint** | Линтинг TypeScript/React |
| **TypeScript** | Проверка типов frontend |
| **Hadolint** | Линтинг Dockerfile |
| **Detect secrets** | Поиск секретов в коде |

---

## 🚀 CI/CD

Проект использует GitHub Actions для автоматизации CI/CD процессов.

### Workflow файлы

| Файл | Описание |
|------|----------|
| `backend-ci.yaml` | Проверка backend: lint, type-check, security, tests |
| `frontend-ci.yaml` | Проверка frontend: lint, type-check, build |
| `cd-deploy.yaml` | Деплой на сервер через SSH |
| `ci-all.yaml` | Оркестрация всех проверок |

### Триггеры

- **CI**: Запускается при push в ветки `main`, `develop` и pull requests
- **CD**: Запускается при push в ветку `main` или вручную через UI

### Проверки

#### Backend CI
- ✅ Ruff lint & format
- ✅ MyPy type check
- ✅ Bandit security check
- ✅ pip-audit dependencies
- ✅ Dockerfile lint

#### Frontend CI
- ✅ ESLint check
- ✅ TypeScript type check
- ✅ Vite build
- ✅ Dockerfile lint
- ✅ Docker build test

### Настройка CD

Для настройки деплоя необходимо добавить GitHub Secrets:

```bash
# В Settings → Secrets and variables → Actions добавьте:
SERVER_HOST=your-server-ip
SERVER_USERNAME=your-username
SERVER_SSH_KEY=your-private-ssh-key
DEPLOY_PATH=/opt/arizonalavka
```

Подробная инструкция в [`.github/SECRETS.md`](.github/SECRETS.md)

### Статус проверок

[![Backend CI](../../actions/workflows/backend-ci.yaml/badge.svg)](../../actions/workflows/backend-ci.yaml)
[![Frontend CI](../../actions/workflows/frontend-ci.yaml/badge.svg)](../../actions/workflows/frontend-ci.yaml)
[![CD Deploy](../../actions/workflows/cd-deploy.yaml/badge.svg)](../../actions/workflows/cd-deploy.yaml)

---

## 📄 Лицензия

© 2026 Arizona Lavka Marketplace. Все права защищены.

**Лицензия:** Proprietary

---

## 👥 Контакты

- **Техническая поддержка:** evgeniy.sytcevich.glory@gmail.com
- **Документация API:** http://localhost:8000/docs
- **GitHub Issues:** [Сообщить об ошибке](../../issues)

---

**Версия:** 3.1.0
**Последнее обновление:** 2026-03-01
