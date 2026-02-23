"""
Сервис аутентификации через Telegram.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import hashlib
import hmac
import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


def validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[Dict[str, Any]]:
    """
    Проверяет подлинность initData от Telegram.
    
    Args:
        init_data: Строка initData от Telegram WebApp
        bot_token: Токен бота от @BotFather
        
    Returns:
        Данные пользователя если валидно, None если нет
    """
    try:
        # Парсим query string
        parsed = parse_qs(init_data)
        
        # Извлекаем hash
        received_hash = parsed.get('hash', [''])[0]
        if not received_hash:
            logger.warning("No hash in init_data")
            return None
        
        # Проверяем актуальность (не старше 5 минут)
        auth_date = int(parsed.get('auth_date', ['0'])[0])
        if time.time() - auth_date > 300:
            logger.warning("InitData expired")
            return None
        
        # Удаляем hash из данных для проверки
        check_data = {k: v[0] for k, v in parsed.items() if k != 'hash'}
        
        # Сортируем параметры и формируем data_check_string
        data_check_arr = []
        for key in sorted(check_data.keys()):
            value = check_data[key]
            data_check_arr.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_arr)
        
        # Вычисляем секретный ключ
        secret_key = hmac.new(
            b'WebAppData',
            bot_token.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем
        if computed_hash != received_hash:
            logger.warning("InitData hash mismatch")
            return None
        
        # Извлекаем данные пользователя
        user_data = parsed.get('user', [None])[0]
        if user_data:
            import json
            user = json.loads(user_data)
            logger.info(f"Telegram user validated: {user.get('id')}")
            return user
        
        logger.warning("No user data in init_data")
        return None
        
    except Exception as e:
        logger.error(f"InitData validation error: {e}")
        return None


def parse_telegram_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует данные Telegram пользователя в формат для БД.
    
    Args:
        user_data: Данные от Telegram
        
    Returns:
        Словарь с полями для БД
    """
    return {
        "telegram_id": user_data.get("id"),
        "telegram_username": user_data.get("username"),
        "telegram_first_name": user_data.get("first_name"),
        "telegram_last_name": user_data.get("last_name"),
        "telegram_language_code": user_data.get("language_code"),
        "is_telegram_user": True,
    }
