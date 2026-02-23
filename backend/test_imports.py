"""
Тестовый скрипт для проверки импортов и запуска backend.
"""

import sys
import traceback
import os

# Установка кодировки UTF-8 для Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_import(module_name: str) -> bool:
    """Проверяет импорт модуля."""
    try:
        __import__(module_name)
        print(f"[OK] {module_name}")
        return True
    except Exception as e:
        print(f"[ERROR] {module_name}: {e}")
        traceback.print_exc()
        return False


def main():
    """Запускает проверку всех импортов."""
    print("=" * 60)
    print("ПРОВЕРКА ИМПОРТОВ BACKEND")
    print("=" * 60)
    
    modules = [
        "config",
        "database",
        "models",
        "dependencies",
        "services.marketplace_service",
        "services.lavka_service",
        "services.auth_service",
        "services.historical_data_service",
        "services.config_generator_service",
        "services.telegram_auth_service",
        "routes.auth",
        "routes.config",
        "routes.marketplace",
        "routes.user",
        "routes.telegram_auth",
        "main",
    ]
    
    results = []
    for module in modules:
        results.append(test_import(module))
    
    print("=" * 60)
    print(f"УСПЕШНО: {sum(results)}/{len(results)}")
    print(f"ОШИБКИ: {len(results) - sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\nВСЕ ИМПОРТЫ РАБОТАЮТ!")
        return 0
    else:
        print("\nЕСТЬ ОШИБКИ В ИМПОРТАХ!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
