"""
Arizona Lavka Marketplace API v3.0

FastAPI backend с аутентификацией, историческими данными
и улучшенной генерацией конфигов.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import logging
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, Tuple

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings, Settings
from database import DatabaseManager, Base

# =============================================================================
# Logging Configuration
# =============================================================================

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# Global State
# =============================================================================

# Rate limiting хранилище: IP -> (количество запросов, timestamp)
# Ограничиваем размер хранилища для предотвращения утечки памяти
MAX_RATE_LIMIT_STORE_SIZE = 10000
rate_limit_store: Dict[str, Tuple[int, float]] = {}


def _cleanup_rate_limit_store(current_time: float) -> None:
    """
    Очищает старые записи из rate_limit_store для предотвращения утечки памяти.
    
    Args:
        current_time: Текущее время в секундах
    """
    # Удаляем записи старше 2 минут
    expiry_time = current_time - 120
    to_delete = [ip for ip, (_, timestamp) in rate_limit_store.items() if timestamp < expiry_time]
    
    for ip in to_delete:
        del rate_limit_store[ip]
    
    # Если хранилище переполнено, удаляем oldest entries
    if len(rate_limit_store) > MAX_RATE_LIMIT_STORE_SIZE:
        # Сортируем по timestamp и оставляем только свежие
        sorted_ips = sorted(rate_limit_store.items(), key=lambda x: x[1][1])
        for ip, _ in sorted_ips[:MAX_RATE_LIMIT_STORE_SIZE // 2]:
            del rate_limit_store[ip]

# Менеджер базы данных
db_manager: DatabaseManager = None


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.
    
    Инициализирует:
    - Подключение к базе данных
    - Кэширование
    - Внешние сервисы
    
    При завершении:
    - Закрывает подключения к БД
    - Очищает ресурсы
    """
    global db_manager
    
    settings = get_settings()
    
    logger.info("=" * 60)
    logger.info(f"Запуск {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Database: PostgreSQL ({settings.POSTGRES_HOST}:{settings.POSTGRES_PORT})")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info("=" * 60)
    
    # Инициализация базы данных
    logger.info("Инициализация подключения к базе данных...")
    db_manager = DatabaseManager(settings.database_url, echo=settings.DEBUG)
    
    try:
        await db_manager.initialize()
        logger.info("База данных успешно инициализирована ✓")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise
    
    # Сохраняем db_manager в state приложения
    app.state.db_manager = db_manager
    
    # Логирование конфигурации
    logger.info(f"CORS Origins: {settings.cors_origins_parsed}")
    logger.info(f"Rate Limit: {settings.RATE_LIMIT_PER_MINUTE} запросов/мин")
    
    yield
    
    # Завершение работы
    logger.info("Остановка приложения...")
    
    if db_manager:
        await db_manager.close()
        logger.info("Подключение к базе данных закрыто ✓")
    
    logger.info("Приложение остановлено")


# =============================================================================
# Application Initialization
# =============================================================================

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Arizona Lavka Marketplace API v3.0

BFF (Backend-For-Frontend) для marketplace Arizona RP (GTA 5 Online).

### 🔍 Возможности:
- **Мониторинг marketplace** - поиск и фильтрация предложений по 33 серверам
- **Умный поиск** - фильтрация по названию предмета, серверу, цене
- **Просмотр лавок** - детальная информация о лавках игроков
- **Генерация конфигов** - IQR анализ + исторические данные + тренды
- **История конфигов** - сохранение и управление сгенерированными конфигами
- **JWT аутентификация** - access/refresh токены

### 🛠️ Технологии:
- FastAPI + SQLAlchemy (async)
- PostgreSQL + AsyncPG
- JWT аутентификация
- TTL кэширование (30 сек)
- IQR фильтрация выбросов
- Анализ исторических данных (66 файлов, 33 сервера)
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# =============================================================================
# Middleware
# =============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_parsed,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware для логирования запросов.

    Логирует:
    - Метод и путь запроса
    - Статус код ответа
    - Время обработки
    """
    start_time = time.time()

    logger.info(f"{request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")

    # Очистка кэша сервисов после запроса для предотвращения утечки памяти
    from dependencies import _service_cache
    _service_cache.clear()

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware для защиты от brute-force и DDoS.

    Ограничивает количество запросов до RATE_LIMIT_PER_MINUTE в минуту.
    Пропускает health check endpoints.
    
    Note:
        Реализует автоматическую очистку старых записей для предотвращения
        утечки памяти. Использует sliding window в 60 секунд.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Пропускаем rate limit для health check и docs
    if request.url.path in ["/", "/health", "/api/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    current_time = time.time()
    
    # Периодическая очистка хранилища (каждые 100 запросов)
    if len(rate_limit_store) % 100 == 0:
        _cleanup_rate_limit_store(current_time)
    
    requests_count, window_start = rate_limit_store.get(client_ip, (0, 0))

    # Сбрасываем счётчик если прошла минута
    if current_time - window_start > 60:
        rate_limit_store[client_ip] = (1, current_time)
    else:
        # Проверяем лимит
        if requests_count >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много запросов. Попробуйте через минуту.",
                headers={"Retry-After": "60"},
            )
        rate_limit_store[client_ip] = (requests_count + 1, window_start)

    return await call_next(request)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "detail": "Внутренняя ошибка сервера", "status_code": 500},
    )


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """
    Корневой endpoint с информацией о сервисе.
    
    Returns:
        dict: Информация о сервисе
    """
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "port": settings.PORT,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Статус здоровья сервиса
    """
    return {
        "status": "healthy",
        "service": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
    }


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """
    API health check endpoint.
    
    Returns:
        dict: Статус здоровья API
    """
    return {
        "status": "ok",
        "service": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
    }


# =============================================================================
# Router Registration
# =============================================================================

from routes import auth_router, config_router, marketplace_router, user_router

app.include_router(auth_router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(config_router, prefix="/api/config", tags=["⚙️ Config Generator"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["🏪 Marketplace"])
app.include_router(user_router, prefix="/api/user", tags=["👤 User"])


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True,
    )
