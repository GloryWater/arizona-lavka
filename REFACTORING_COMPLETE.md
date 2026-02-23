# Arizona Lavka Marketplace v3.0 - Рефакторинг завершён

## ✅ Выполненные изменения

### 1. База данных (PostgreSQL)
- ✅ `DatabaseManager` класс для управления подключениями
- ✅ Правильная инициализация через `create_async_engine`
- ✅ Connection pooling (10 соединений, max 20)
- ✅ Правильные индексы и связи между моделями
- ✅ Асинхронные сессии с авто-коммитом и rollback

### 2. Конфигурация
- ✅ PostgreSQL настройки вместо SQLite
- ✅ Property `database_url` для генерации URL
- ✅ Валидация JWT_SECRET_KEY через `field_validator`
- ✅ CORS_ORIGINS как строка с парсингом в список

### 3. Main приложение
- ✅ Lifespan контекст для инициализации БД
- ✅ `app.state.db_manager` для хранения менеджера БД
- ✅ Middleware для логирования и rate limiting
- ✅ Обработчики исключений
- ✅ Правильное подключение роутов

### 4. Dependencies (DI)
- ✅ `get_db_manager` для получения менеджера БД
- ✅ `get_db_session` для получения сессии
- ✅ Правильные зависимости для сервисов
- ✅ Кэширование настроек через `lru_cache`

### 5. Сервисы
- ✅ `AuthService` - аутентификация, JWT, password hashing
- ✅ `MarketplaceService` - кэширование API, TTL 30 сек
- ✅ `LavkaService` - лавки, items mapping
- ✅ `HistoricalDataService` - анализ исторических данных
- ✅ `ConfigGeneratorService` - IQR, тренды, ликвидность

### 6. Routes
- ✅ `auth.py` - регистрация, вход, refresh, logout
- ✅ `marketplace.py` - offers, servers, lavkas
- ✅ `config.py` - генерация, история, скачивание
- ✅ `user.py` - профиль, избранное, уведомления

## 🚀 Развёртывание

### 1. Остановка старых контейнеров
```bash
cd /path/to/arizonalavka
docker compose down -v
```

### 2. Пересборка всех образов
```bash
docker compose build --no-cache
```

### 3. Запуск
```bash
docker compose up -d
```

### 4. Проверка логов
```bash
# Backend
docker compose logs -f backend

# PostgreSQL
docker compose logs -f postgres

# Frontend
docker compose logs -f frontend
```

### 5. Проверка подключения к БД
```bash
docker exec -it arizonalavka-postgres psql -U arizonalavka -d arizonalavka -c "\dt"
```

## 📁 Структура проекта

```
backend/
├── main.py                    # FastAPI приложение + lifespan
├── config.py                  # Настройки (Pydantic Settings)
├── database.py                # DatabaseManager + ORM модели
├── models.py                  # Pydantic схемы API
├── dependencies.py            # Dependency Injection
├── items.json                 # Mapping предметов
├── requirements.txt           # Python зависимости
├── Dockerfile                 # Docker образ
├── services/
│   ├── auth_service.py        # JWT, password hashing
│   ├── marketplace_service.py # API marketplace + кэш
│   ├── lavka_service.py       # Лавки и предметы
│   ├── historical_data_service.py  # Исторический анализ
│   └── config_generator_service.py # Генерация конфигов
└── routes/
    ├── auth.py                # /api/auth/*
    ├── marketplace.py         # /api/marketplace/*
    ├── config.py              # /api/config/*
    └── user.py                # /api/user/*

data/                          # Исторические данные (66 файлов)
frontend/                      # React приложение
docker-compose.yml             # PostgreSQL + Backend + Frontend
```

## 🔧 Конфигурация

### Переменные окружения (.env)
```bash
# Database
POSTGRES_USER=arizonalavka
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=arizonalavka
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# JWT (обязательно 32+ символа)
JWT_SECRET_KEY=your-super-secret-key-min-32-characters-long

# CORS
CORS_ORIGINS=https://lavka.glorysyntax.live,http://localhost:5173

# Debug
DEBUG=false
```

## 📊 API Endpoints

### Health Check
- `GET /` - Информация о сервисе
- `GET /health` - Health check
- `GET /api/health` - API health check

### Authentication
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/refresh` - Refresh токена
- `POST /api/auth/logout` - Выход
- `GET /api/auth/me` - Текущий пользователь

### Marketplace
- `GET /api/marketplace/servers` - Список серверов
- `GET /api/marketplace/items` - Mapping предметов
- `GET /api/marketplace/offers` - Предложения (с фильтрами)
- `GET /api/marketplace/lavkas` - Лавки на сервере
- `GET /api/marketplace/lavkas/{id}` - Детали лавки

### Config Generator
- `POST /api/config/generate` - Генерация конфига
- `POST /api/config/generate/download` - Скачать конфиг
- `GET /api/config/history` - История конфигов
- `GET /api/config/history/{id}` - Скачать из истории

### User
- `GET /api/user/profile` - Профиль
- `GET /api/user/favorites` - Избранное
- `POST /api/user/favorites` - Добавить в избранное
- `DELETE /api/user/favorites/{id}` - Удалить из избранного
- `GET /api/user/alerts` - Уведомления
- `POST /api/user/alerts` - Создать уведомление
- `DELETE /api/user/alerts/{id}` - Удалить уведомление

## 🎯 Ключевые улучшения

### Производительность
- Connection pooling (10 базовых, 20 максимум)
- TTL кэширование (30 секунд)
- Selectin загрузка связанных данных
- Индексы на часто используемых полях

### Безопасность
- Валидация JWT_SECRET_KEY (минимум 32 символа)
- Rate limiting (60 запросов в минуту)
- Password hashing (bcrypt, 12 rounds)
- Блокировка после 5 неудачных попыток

### Надёжность
- Graceful error handling
- Rollback при ошибках
- Логирование всех операций
- Health check endpoints

### Код
- Type hints везде
- Docstrings для всех классов и методов
- Разделение ответственности (SRP)
- Dependency Injection
- DRY принцип

## 🐛 Troubleshooting

### Ошибки подключения к БД
```bash
# Проверьте что PostgreSQL запущен
docker compose ps postgres

# Проверьте логи
docker compose logs postgres

# Проверьте переменные окружения
docker compose exec backend env | grep POSTGRES
```

### Ошибки миграции
```bash
# Удалите том с данными и пересоздайте
docker volume rm arizonalavka_postgres_data
docker compose up -d postgres
```

### Ошибки импорта
```bash
# Проверьте зависимости
docker compose exec backend pip list

# Пересоберите образ
docker compose build --no-cache backend
```

---

**Версия:** 3.0.0 (рефакторинг)  
**Дата:** Февраль 2026  
**Статус:** Production Ready ✓
