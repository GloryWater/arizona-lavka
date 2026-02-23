# 🚀 Инструкция по деплою Arizona Lavka Marketplace

## Требования
- Docker 20+
- Docker Compose 2.0+
- Сервер с Linux (Ubuntu 20.04+ рекомендуется)

## 📦 Быстрый старт

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose (если не установлен)
sudo apt install docker-compose -y

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
# Выйдите и войдите заново для применения изменений
```

### 2. Загрузка проекта

```bash
# Клонирование репозитория или загрузка файлов
# Скопируйте файлы проекта на сервер в директорию /opt/arizonalavka
```

### 3. Настройка переменных окружения

```bash
cd /opt/arizonalavka

# Копирование .env.example в .env
cp .env.example .env

# Генерация безопасных секретов
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Редактирование .env файла
nano .env
```

### 4. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

## 🔧 Доступ к приложению

После запуска:
- **Frontend:** http://your-server-ip
- **Backend API:** http://your-server-ip:8000
- **API Docs:** http://your-server-ip:8000/docs

## 🗄️ База данных

### Резервное копирование

```bash
# Создание дампа базы данных
docker exec arizonalavka-postgres pg_dump -U arizonalavka arizonalavka > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из дампа
docker exec -i arizonalavka-postgres psql -U arizonalavka arizonalavka < backup_YYYYMMDD_HHMMSS.sql
```

### Подключение к БД

```bash
# Подключение к PostgreSQL
docker exec -it arizonalavka-postgres psql -U arizonalavka -d arizonalavka
```

## 📊 Мониторинг

```bash
# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats

# Логи backend
docker compose logs -f backend

# Логи frontend
docker compose logs -f frontend

# Логи PostgreSQL
docker compose logs -f postgres
```

## 🔄 Обновление

```bash
# Остановка старых контейнеров
docker compose down

# Сборка новых образов
docker compose build --no-cache

# Запуск новых контейнеров
docker compose up -d

# Очистка старых образов
docker image prune -f
```

## 🔐 Настройка HTTPS (опционально)

### Установка Nginx с SSL

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление сертификатов
sudo certbot renew --dry-run
```

### Конфигурация Nginx reverse proxy

Создайте файл `/etc/nginx/sites-available/arizonalavka`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Включение конфигурации
sudo ln -s /etc/nginx/sites-available/arizonalavka /etc/nginx/sites-enabled/

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
```

## 🛡️ Безопасность

### Изменение паролей по умолчанию

В `docker-compose.yml` измените:
- `POSTGRES_PASSWORD` - сложный пароль для БД

В `.env` измените:
- `JWT_SECRET_KEY` - минимум 32 символа
- `JWT_REFRESH_SECRET_KEY` - минимум 32 символа

### Firewall

```bash
# Установка UFW
sudo apt install ufw -y

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTP/HTTPS
sudo ufw allow http
sudo ufw allow https

# Включение firewall
sudo ufw enable
```

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверка логов
docker compose logs backend

# Проверка подключения к БД
docker exec arizonalavka-backend python -c "from config import get_settings; print(get_settings().database_url)"
```

### Frontend не загружается

```bash
# Пересборка frontend
docker compose build frontend
docker compose up -d frontend
```

### Ошибки базы данных

```bash
# Проверка статуса БД
docker exec arizonalavka-postgres pg_isready

# Перезапуск PostgreSQL
docker compose restart postgres
```

### Сброс базы данных (ВСЕ ДАННЫЕ БУДУТ УДАЛЕНЫ!)

```bash
# Остановка сервисов
docker compose down

# Удаление volume с данными
docker volume rm arizonalavka-postgres_data

# Запуск заново
docker compose up -d
```

## 📈 Производительность

### Оптимизация PostgreSQL

Добавьте в `docker-compose.yml` для postgres:

```yaml
command: >
  postgres
  -c shared_buffers=256MB
  -c effective_cache_size=768MB
  -c work_mem=16MB
  -c maintenance_work_mem=128MB
```

### Кэширование статики

Nginx уже настроен на кэширование статических файлов на 1 год.

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker compose logs -f`
2. Убедитесь, что все переменные окружения установлены
3. Проверьте доступность портов: `netstat -tlnp`

---

**Версия:** 3.0.0  
**Дата:** Февраль 2026
