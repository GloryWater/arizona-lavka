# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Копирование package файлов для кэширования зависимостей
COPY package*.json ./

# Установка зависимостей с оптимизацией для сборки без кэша
# --prefer-offline: использует локальный кэш если доступен
# --no-audit: пропускает проверку уязвимостей (ускоряет установку)
# --no-fund: пропускает сообщения о спонсировании пакетов
RUN npm ci --prefer-offline --no-audit --no-fund \
    && npm cache clean --force

# Копирование исходного кода
COPY . .

# Создаём .env файл с API URL для сборки
RUN echo "VITE_API_URL=/api" > .env

# Сборка приложения
RUN npm run build

# Production stage
FROM nginx:alpine

# Копирование собранного приложения из builder stage
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
