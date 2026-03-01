#!/bin/bash
# Скрипт для запуска нагрузочных тестов

set -e

HOST="${HOST:-https://lavka.glorysyntax.live}"
USERS="${USERS:-50}"
RATE="${RATE:-5}"
DURATION="${DURATION:-180s}"

echo "============================================"
echo "Нагрузочное тестирование Arizona Lavka"
echo "============================================"
echo "Хост: $HOST"
echo "Пользователей: $USERS"
echo "Скорость спавна: $RATE users/sec"
echo "Длительность: $DURATION"
echo "============================================"

# Проверка установленного locust
if ! command -v locust &> /dev/null; then
    echo "❌ Locust не найден. Установка..."
    pip install locust
fi

# Создание директории для результатов
mkdir -p load_tests/results

# Запуск теста
echo ""
echo "🚀 Запуск теста..."
echo ""

locust -f load_tests/locustfile.py \
    --host "$HOST" \
    --headless \
    -u "$USERS" \
    -r "$RATE" \
    -t "$DURATION" \
    --csv "load_tests/results/test_$(date +%Y%m%d_%H%M%S)_" \
    --html "load_tests/results/report_$(date +%Y%m%d_%H%M%S).html"

echo ""
echo "============================================"
echo "✅ Тест завершён!"
echo "Результаты сохранены в load_tests/results/"
echo "============================================"
