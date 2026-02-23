# Подключение к PostgreSQL базе данных

## 📋 Параметры подключения

```
Host: localhost (через SSH туннель)
Port: 5432
Database: arizonalavka
Username: arizonalavka
Password: arizonalavka_password
```

---

## 🔐 Шаг 1: Применение изменений на сервере

1. **Загрузите изменения на сервер:**
```bash
# На вашем локальном ПК
git add docker-compose.yml
git commit -m "Add PostgreSQL port forwarding"
git push origin master
```

2. **На сервере выполните:**
```bash
cd /path/to/arizonalavka  # Путь к проекту на сервере
git pull origin master

# Перезапустите контейнеры
docker-compose down
docker-compose up -d

# Проверьте статус
docker-compose ps
```

3. **Проверьте, что порт открыт:**
```bash
# На сервере
docker port arizonalavka-postgres
# Должно показать: 5432/tcp -> 127.0.0.1:5432
```

---

## 🔹 Способ 1: Подключение через SSH туннель (рекомендуется)

### Шаг 1.1: Создайте SSH туннель

Откройте **новый терминал** на вашем ПК:

```bash
# Windows PowerShell / Linux / macOS
ssh -L 5432:localhost:5432 user@ваш-сервер.com

# Пример:
ssh -L 5432:localhost:5432 root@lavka.glorysyntax.live
```

**Окно терминала должно оставаться открытым!**

### Шаг 1.2: Подключитесь к базе

**Вариант A: Через psql (командная строка)**

Откройте **второй терминал** (первый с SSH туннелем не закрывайте):

```bash
psql -h localhost -p 5432 -U arizonalavka -d arizonalavka
# Введите пароль: arizonalavka_password
```

**Вариант B: Через DBeaver**

1. Откройте DBeaver
2. Создайте новое подключение → PostgreSQL
3. Заполните параметры:
   - **Host:** `localhost`
   - **Port:** `5432`
   - **Database:** `arizonalavka`
   - **Username:** `arizonalavka`
   - **Password:** `arizonalavka_password`
4. Нажмите "Test Connection" → "OK"

**Вариант C: Через pgAdmin**

1. Откройте pgAdmin
2. Правый клик на "Servers" → "Register" → "Server"
3. Вкладка "General":
   - **Name:** `ArizonaLavka DB`
4. Вкладка "Connection":
   - **Host name/address:** `localhost`
   - **Port:** `5432`
   - **Maintenance database:** `arizonalavka`
   - **Username:** `arizonalavka`
   - **Password:** `arizonalavka_password`
5. Нажмите "Save"

---

## 🔹 Способ 2: Прямое подключение через Docker на сервере

Если нужно быстро выполнить запрос:

```bash
# Подключиться к контейнеру
docker exec -it arizonalavka-postgres psql -U arizonalavka -d arizonalavka

# Выполнить команду без интерактивного режима
docker exec arizonalavka-postgres psql -U arizonalavka -d arizonalavka -c "SELECT * FROM users LIMIT 10;"
```

---

## 🔹 Способ 3: Подключение из Python скрипта

```python
import psycopg2

# Через SSH туннель (порт 5432 проброшен на localhost)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="arizonalavka",
    user="arizonalavka",
    password="arizonalavka_password"
)

cur = conn.cursor()
cur.execute("SELECT * FROM users LIMIT 10;")
print(cur.fetchall())

cur.close()
conn.close()
```

---

## 🛠️ Полезные SQL запросы

```sql
-- Показать все таблицы
\dt

-- Показать структуру таблицы
\d users

-- Показать всех пользователей
SELECT id, username, email, created_at FROM users;

-- Показать количество конфигов по пользователям
SELECT u.username, COUNT(c.id) as config_count
FROM users u
LEFT JOIN config_history c ON u.id = c.user_id
GROUP BY u.id, u.username
ORDER BY config_count DESC;

-- Показать последние конфиги
SELECT id, server_name, mode, percentage, items_count, created_at
FROM config_history
ORDER BY created_at DESC
LIMIT 10;

-- Показать избранные предметы
SELECT u.username, f.item_name, f.target_price, f.mode
FROM favorite_items f
JOIN users u ON f.user_id = u.id
WHERE f.is_active = true;
```

---

## ❌ Устранение проблем

### Ошибка: "Connection refused"

1. Проверьте, что SSH туннель активен
2. Проверьте, что контейнер запущен:
```bash
docker-compose ps
```

### Ошибка: "Password authentication failed"

Проверьте пароль в `docker-compose.yml`:
```yaml
environment:
  POSTGRES_PASSWORD: arizonalavka_password  # Должен совпадать
```

### Ошибка: "Database does not exist"

База данных создаётся автоматически при первом запуске. Если проблема остаётся:
```bash
# Перезапустите контейнер
docker-compose restart postgres

# Проверьте логи
docker-compose logs postgres
```

---

## 🔒 Безопасность

⚠️ **Порт PostgreSQL открыт только на localhost (127.0.0.1)**

Это означает:
- ✅ Можно подключаться через SSH туннель
- ✅ Нельзя подключиться напрямую из интернета
- ✅ Безопасно для production

**Не изменяйте `127.0.0.1:5432:5432` на `5432:5432`** — это откроет порт для всех!

---

## 📊 Структура базы данных

### Таблицы:

| Таблица | Описание |
|---------|----------|
| `users` | Пользователи |
| `config_history` | История сгенерированных конфигов |
| `favorite_items` | Избранные предметы |
| `price_alerts` | Уведомления об изменении цен |
| `audit_logs` | Журнал аудита действий |

### Основные поля:

**users:**
- `id`, `username`, `email`, `hashed_password`
- `is_premium`, `created_at`, `updated_at`

**config_history:**
- `id`, `user_id`, `server_id`, `server_name`
- `mode`, `percentage`, `items_count`
- `config_data` (JSON), `created_at`

**favorite_items:**
- `id`, `user_id`, `item_id`, `item_name`
- `target_price`, `mode`, `server_id`
- `is_active`, `created_at`

---

## 📞 Поддержка

При возникновении проблем проверьте логи:
```bash
# Логи PostgreSQL
docker-compose logs postgres

# Логи backend
docker-compose logs backend
```
