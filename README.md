# Arizona Lavka Marketplace v3.0

Профессиональная full-stack платформа для мониторинга и анализа marketplace игрового сервера Arizona RP (GTA 5 Online).

## 🚀 Возможности

- **Мониторинг marketplace** в реальном времени
- **Поиск предметов** по названию с фильтрацией
- **Фильтрация по серверам** (33 сервера Arizona RP)
- **Сортировка по цене** (возрастание/убывание)
- **Просмотр лавок** игроков с детальной информацией
- **Генерация торговых конфигов** с IQR фильтрацией выбросов
- **Исторический анализ данных** (тренды, ликвидность)
- **JWT аутентификация** с refresh токенами
- **История сгенерированных конфигов**

## 📋 Требования

- Docker 20+
- Docker Compose 2.0+

## 🛠️ Технологический стек

### Backend
- **Python 3.12**
- **FastAPI 0.109+**
- **SQLAlchemy 2.0** (async)
- **PostgreSQL 15**
- **PyJWT** (аутентификация)
- **bcrypt** (хеширование паролей)
- **HTTPX** (HTTP клиент)
- **Cachetools** (кэширование)

### Frontend
- **React 18**
- **TypeScript 5**
- **Vite 5**
- **Tailwind CSS 3**
- **React Router 7**
- **Axios**
- **Lucide React** (иконки)

### Infrastructure
- **Docker**
- **Docker Compose**
- **Nginx** (production)

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd arizonalavka
```

### 2. Настройка переменных окружения

```bash
# Скопируйте файл .env.example в .env
cp .env.example .env

# Отредактируйте .env и установите свои значения
# ОСОБЕННО ВАЖНО: измените JWT_SECRET_KEY и JWT_REFRESH_SECRET_KEY
```

### 3. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 🌐 Доступ

После запуска приложение будет доступно по адресу:

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## 📁 Структура проекта

```
arizonalavka/
├── backend/                      # Backend приложение
│   ├── main.py                   # FastAPI приложение
│   ├── config.py                 # Настройки
│   ├── database.py               # SQLAlchemy модели
│   ├── models.py                 # Pydantic схемы
│   ├── items.json                # Mapping предметов
│   ├── requirements.txt          # Python зависимости
│   ├── Dockerfile                # Docker образ
│   ├── services/                 # Бизнес-логика
│   │   ├── auth_service.py       # JWT аутентификация
│   │   ├── marketplace_service.py # API marketplace
│   │   ├── historical_data_service.py  # Исторический анализ
│   │   └── advanced_config_generator.py  # IQR генератор
│   └── routes/                   # API endpoints
│       ├── auth.py               # /api/auth/*
│       ├── marketplace.py        # /api/marketplace/*
│       ├── config.py             # /api/config/*
│       └── user.py               # /api/user/*
│
├── frontend/                     # Frontend приложение
│   ├── src/
│   │   ├── App.tsx               # Корневой компонент
│   │   ├── main.tsx              # Entry point
│   │   ├── types.ts              # TypeScript типы
│   │   ├── api/
│   │   │   └── marketplace.ts    # Axios клиент
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx   # Auth состояние
│   │   ├── pages/                # Страницы
│   │   ├── components/           # UI компоненты
│   │   └── utils/                # Утилиты
│   ├── Dockerfile                # Docker образ
│   └── nginx.conf                # Nginx конфигурация
│
├── docker-compose.yml            # Docker оркестрация
├── .env.example                  # Шаблон окружения
└── README.md                     # Документация
```

## 🔧 API Endpoints

### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/refresh` - Обновление токена
- `POST /api/auth/logout` - Выход
- `GET /api/auth/me` - Информация о пользователе

### Marketplace
- `GET /api/marketplace/offers` - Предложения
- `GET /api/marketplace/servers` - Список серверов
- `GET /api/marketplace/lavkas` - Лавки на сервере
- `GET /api/marketplace/lavkas/{lavka_uid}` - Детали лавки
- `GET /api/marketplace/items` - Mapping предметов

### Генератор конфигов
- `POST /api/config/generate/download` - Генерация и скачивание конфига
- `GET /api/config/history` - История конфигов
- `GET /api/config/history/{config_id}` - Скачивание конфига из истории

### Пользователь
- `GET /api/user/profile` - Профиль пользователя
- `GET /api/user/favorites` - Избранные предметы
- `POST /api/user/favorites` - Добавить в избранное
- `DELETE /api/user/favorites/{id}` - Удалить из избранного
- `GET /api/user/alerts` - Уведомления
- `POST /api/user/alerts` - Создать уведомление
- `DELETE /api/user/alerts/{id}` - Удалить уведомление

## 🔐 Безопасность

### Требования к паролям
- Минимальная длина: 8 символов
- Хеширование: bcrypt с солью (12 rounds)

### Защита от brute-force
- Максимум попыток входа: 5
- Время блокировки: 15 минут

### JWT токены
- Access token: 30 минут
- Refresh token: 7 дней

## ⚙️ Генерация конфигов

Генератор использует продвинутый алгоритм с:
1. **IQR фильтрация** выбросов для точного расчёта медианы
2. **Исторический анализ** за 7 и 30 дней
3. **Расчёт тренда** цены (рост/падение/стабильно)
4. **Оценка ликвидности** предмета (0-100)
5. **Взвешенный расчёт** справедливой цены
6. **Оценка уверенности** (VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW)

### Веса для расчёта цены
- Текущая цена: 40%
- Историческая цена: 35%
- Тренд: 25%

## 📝 Логи

Логи приложения сохраняются в stdout/stderr контейнера backend.

Просмотр логов:
```bash
docker-compose logs -f backend
```

## 🗄️ База данных

### Модели
- **User** - Пользователи
- **ConfigHistory** - История конфигов
- **FavoriteItem** - Избранные предметы
- **PriceAlert** - Уведомления о ценах
- **AuditLog** - Журнал аудита

### Резервное копирование
```bash
# Создание дампа
docker exec arizonalavka-postgres pg_dump -U arizonalavka arizonalavka > backup.sql

# Восстановление
docker exec -i arizonalavka-postgres psql -U arizonalavka arizonalavka < backup.sql
```

## 🚀 Production развёртывание

### 1. Настройка сервера

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt install docker-compose -y
```

### 2. Настройка .env

```bash
# Сгенерируйте безопасные секреты
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)

# Установите сложный пароль для БД
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### 3. Настройка Nginx (опционально)

Если требуется HTTPS, настройте reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Запуск

```bash
docker-compose up -d
```

## 🧪 Разработка

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📄 Лицензия

Proprietary - Все права защищены.

## 📞 Поддержка

По вопросам обращайтесь к разработчику.

---

**Версия:** 3.0.0  
**Дата:** Февраль 2026
