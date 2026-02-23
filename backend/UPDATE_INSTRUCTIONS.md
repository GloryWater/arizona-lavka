# Инструкция по обновлению зависимостей

## Важно! Изменения в backend зависимостях

В версии v3.1 произведена миграция с устаревшей `passlib` на прямое использование `bcrypt`.

### 🔧 Что нужно сделать

#### 1. Обновить зависимости

```bash
cd backend

# Если используете venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Пересоздать зависимости
pip uninstall passlib -y
pip install -r requirements.txt --upgrade
```

#### 2. Проверить работу

```bash
# Проверка bcrypt
python -c "from services.auth_service import get_password_hash; print(get_password_hash('test'))"

# Запуск сервера
python -m uvicorn main:app --reload
```

### ⚠️ Важные замечания

1. **Старые пароли** будут работать автоматически - bcrypt совместим с форматом passlib
2. **Новые пароли** будут хешироваться с раундами 12 (более безопасно)
3. **Миграция БД не требуется** - формат хешей совместим

### 📦 Изменения в requirements.txt

**Удалено:**
- `passlib[bcrypt]>=1.7.4`

**Осталось:**
- `bcrypt>=4.1.0`

### 🚀 Почему это сделано

- `passlib` больше не поддерживается (последний релиз в 2020)
- Прямое использование `bcrypt` проще и надёжнее
- Исправлена ошибка: "password cannot be longer than 72 bytes"
- Лучшая совместимость с Python 3.12+

---

**© 2026 Arizona Lavka Marketplace**
