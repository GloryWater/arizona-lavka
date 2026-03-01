"""
Админ-панель - роуты для управления пользователями, логами и настройками.

© 2026 Arizona Lavka Marketplace. Все права защищены.
Лицензия: Proprietary
"""

import csv
import io
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, ConfigHistory, AdminLog, GlobalSetting
from dependencies import get_db_session, get_current_admin
from models import (
    AdminUserResponse,
    AdminLogResponse,
    AdminStatsSummary,
    AdminStatsChartData,
    GlobalSettingResponse,
    GlobalSettingUpdate,
    AuditLogResponse,
)
from services.audit_log_service import AuditLogService

router = APIRouter()
logger = logging.getLogger(__name__)

# Кэш для настроек в памяти
_settings_cache: dict = {}
_settings_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 60


def get_auth_service(
    session: AsyncSession = Depends(get_db_session)
):
    """Создаёт экземпляр AuthService."""
    from services.auth_service import AuthService
    from config import get_settings
    return AuthService(session, get_settings())


# =============================================================================
# Users Management
# =============================================================================

@router.get("/users", response_model=List[AdminUserResponse])
async def get_users(
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=100, ge=1, le=500, description="Лимит на странице"),
    search: Optional[str] = Query(default=None, max_length=100, description="Поиск по id или username"),
    sort_by: str = Query(default="created_at", description="Сортировка: created_at, username, configs_count"),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение списка пользователей с пагинацией и фильтрацией.
    
    - **page**: Номер страницы (начиная с 1)
    - **limit**: Количество элементов на странице (макс. 500)
    - **search**: Поиск по ID или username
    - **sort_by**: Поле для сортировки
    """
    # Базовый запрос
    query = select(User)
    
    # Поиск
    if search:
        # Пробуем найти по ID (если search - число)
        if search.isdigit():
            query = query.where(
                (User.username.ilike(f"%{search}%")) | (User.id == int(search))
            )
        else:
            query = query.where(User.username.ilike(f"%{search}%"))
    
    # Сортировка
    if sort_by == "username":
        query = query.order_by(User.username)
    elif sort_by == "configs_count":
        # Сортировка по количеству конфигов через подзапрос
        configs_count_subquery = (
            select(func.count(ConfigHistory.id))
            .where(ConfigHistory.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )
        query = query.order_by(desc(configs_count_subquery))
    else:  # created_at
        query = query.order_by(desc(User.created_at))
    
    # Пагинация
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Выполняем запрос
    result = await session.execute(query)
    users = result.scalars().all()
    
    # Получаем количество конфигов для каждого пользователя
    users_with_configs = []
    for user in users:
        configs_count_result = await session.execute(
            select(func.count(ConfigHistory.id)).where(ConfigHistory.user_id == user.id)
        )
        configs_count = configs_count_result.scalar_one() or 0
        
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_premium": user.is_premium,
            "role": user.role,
            "last_active_at": user.last_active_at,
            "created_at": user.created_at,
            "configs_count": configs_count,
        }
        users_with_configs.append(AdminUserResponse(**user_dict))
    
    # Логирование действия
    await _log_admin_action(
        session, current_admin, "VIEW_USERS", 
        {"page": page, "limit": limit, "search": search},
        request=None
    )
    
    return users_with_configs


@router.get("/users/export")
async def export_users_to_csv(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Экспорт всех пользователей в CSV формат.
    
    Возвращает файл в формате CSV со всеми пользователями.
    """
    # Получаем всех пользователей
    result = await session.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    
    # Создаём CSV в памяти
    output = io.StringIO()
    fieldnames = [
        "id", "username", "email", "first_name", "last_name",
        "is_premium", "role", "last_active_at", "created_at"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for user in users:
        writer.writerow({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "is_premium": user.is_premium,
            "role": user.role,
            "last_active_at": user.last_active_at.isoformat() if user.last_active_at else "",
            "created_at": user.created_at.isoformat(),
        })
    
    output.seek(0)
    
    # Логирование
    await _log_admin_action(
        session, current_admin, "EXPORT_DATA",
        {"type": "users_csv", "count": len(users)},
        request=None
    )
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"},
    )


# =============================================================================
# Admin Logs
# =============================================================================

@router.get("/logs", response_model=List[AdminLogResponse])
async def get_admin_logs(
    start_date: Optional[datetime] = Query(default=None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(default=None, description="Конечная дата"),
    event_type: Optional[str] = Query(default=None, description="Тип события"),
    search_query: Optional[str] = Query(default=None, description="Поиск по user_id/username"),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=200, description="Лимит на странице"),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение логов админ-панели с фильтрацией.
    
    - **start_date**: Начальная дата (ISO 8601)
    - **end_date**: Конечная дата (ISO 8601)
    - **event_type**: Тип события (LOGIN, LOGOUT, etc.)
    - **search_query**: Поиск по user_id или username
    """
    query = select(AdminLog)
    
    # Фильтры
    conditions = []
    
    if start_date:
        conditions.append(AdminLog.created_at >= start_date)
    
    if end_date:
        conditions.append(AdminLog.created_at <= end_date)
    
    if event_type:
        conditions.append(AdminLog.event_type == event_type)
    
    if search_query:
        if search_query.isdigit():
            conditions.append(AdminLog.user_id == int(search_query))
        else:
            # Поиск по username через join
            user_subquery = select(User.id).where(User.username.ilike(f"%{search_query}%"))
            conditions.append(AdminLog.user_id.in_(user_subquery.scalar_subquery()))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Сортировка по убыванию даты
    query = query.order_by(desc(AdminLog.created_at))
    
    # Пагинация
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Выполняем запрос с join для получения username
    query = query.outerjoin(User, AdminLog.user_id == User.id)
    result = await session.execute(query)
    logs = result.scalars().all()
    
    # Формируем ответ с username
    logs_response = []
    for log in logs:
        username = None
        if log.user_id:
            # Получаем username из уже загруженной сессии
            user = await session.get(User, log.user_id)
            if user:
                username = user.username
        
        logs_response.append(AdminLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            event_type=log.event_type,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at,
        ))
    
    # Логирование просмотра логов
    await _log_admin_action(
        session, current_admin, "VIEW_LOGS",
        {"page": page, "limit": limit, "filters": {"start_date": str(start_date) if start_date else None}},
        request=None
    )

    return logs_response


# =============================================================================
# User Audit Logs
# =============================================================================

@router.get("/logs/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    start_date: Optional[datetime] = Query(default=None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(default=None, description="Конечная дата"),
    action: Optional[str] = Query(default=None, description="Тип действия (USER_REGISTERED, CONFIG_GENERATED, etc.)"),
    search_query: Optional[str] = Query(default=None, description="Поиск по user_id/username"),
    status_filter: Optional[str] = Query(default=None, description="Статус (success, failure, error)"),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=200, description="Лимит на странице"),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение логов аудита пользователей с фильтрацией.

    - **start_date**: Начальная дата (ISO 8601)
    - **end_date**: Конечная дата (ISO 8601)
    - **action**: Тип действия (USER_REGISTERED, USER_LOGGED_IN, CONFIG_GENERATED, etc.)
    - **search_query**: Поиск по user_id или username
    - **status_filter**: Фильтр по статусу (success, failure, error)
    """
    from database import AuditLog

    query = select(AuditLog)

    # Фильтры
    conditions = []

    if start_date:
        conditions.append(AuditLog.created_at >= start_date)

    if end_date:
        conditions.append(AuditLog.created_at <= end_date)

    if action:
        conditions.append(AuditLog.action == action)

    if status_filter:
        conditions.append(AuditLog.status == status_filter)

    if search_query:
        if search_query.isdigit():
            conditions.append(AuditLog.user_id == int(search_query))
        else:
            # Поиск по username через join
            user_subquery = select(User.id).where(User.username.ilike(f"%{search_query}%"))
            conditions.append(AuditLog.user_id.in_(user_subquery.scalar_subquery()))

    if conditions:
        query = query.where(and_(*conditions))

    # Сортировка по убыванию даты
    query = query.order_by(desc(AuditLog.created_at))

    # Пагинация
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Выполняем запрос с join для получения username
    query = query.outerjoin(User, AuditLog.user_id == User.id)
    result = await session.execute(query)
    logs = result.scalars().all()

    # Формируем ответ с username
    logs_response = []
    for log in logs:
        username = None
        if log.user_id:
            # Получаем username из уже загруженной сессии
            user = await session.get(User, log.user_id)
            if user:
                username = user.username

        logs_response.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            details=log.details,
            status=log.status,
            error_message=log.error_message,
            created_at=log.created_at,
        ))

    return logs_response


# =============================================================================
# Statistics
# =============================================================================

@router.get("/stats/summary", response_model=AdminStatsSummary)
async def get_stats_summary(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение сводной статистики.

    Возвращает:
    - **total_users**: Всего пользователей
    - **total_configs**: Всего сгенерированных конфигов
    - **dau**: Активные пользователи за сегодня
    - **mau**: Активные пользователи за 30 дней
    - **avg_configs_per_user_per_day**: Среднее количество конфигов на пользователя в день
    """
    # Всего пользователей
    total_users_result = await session.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar_one() or 0

    # Всего конфигов
    total_configs_result = await session.execute(select(func.count(ConfigHistory.id)))
    total_configs = total_configs_result.scalar_one() or 0

    # DAU - активные за сегодня
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    dau_result = await session.execute(
        select(func.count(func.distinct(User.id))).where(
            User.last_active_at >= today_start
        )
    )
    dau = dau_result.scalar_one() or 0

    # MAU - активные за 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    mau_result = await session.execute(
        select(func.count(func.distinct(User.id))).where(
            User.last_active_at >= thirty_days_ago
        )
    )
    mau = mau_result.scalar_one() or 0

    # Среднее количество конфигов на пользователя в день
    # Считаем конфиги за последние 30 дней и делим на количество уникальных пользователей
    configs_last_30_days_result = await session.execute(
        select(func.count(ConfigHistory.id)).where(
            ConfigHistory.created_at >= thirty_days_ago
        )
    )
    configs_last_30_days = configs_last_30_days_result.scalar_one() or 0
    
    # Среднее = конфиги за 30 дней / (пользователи * 30 дней)
    avg_configs_per_user_per_day = 0.0
    if total_users > 0:
        avg_configs_per_user_per_day = configs_last_30_days / (total_users * 30)

    # Логирование
    await _log_admin_action(
        session, current_admin, "VIEW_STATS",
        {"type": "summary"},
        request=None
    )

    return AdminStatsSummary(
        total_users=total_users,
        total_configs=total_configs,
        dau=dau,
        mau=mau,
        avg_configs_per_user_per_day=round(avg_configs_per_user_per_day, 2),
    )


@router.get("/stats/charts", response_model=List[AdminStatsChartData])
async def get_stats_charts(
    start_date: Optional[datetime] = Query(default=None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(default=None, description="Конечная дата"),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение данных для графиков.

    Группировка по дате:
    - registrations: Количество регистраций
    - configs_generated: Количество сгенерированных конфигов
    """
    from sqlalchemy import Date, text
    
    # Даты по умолчанию (последние 30 дней)
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Получаем регистрации по дням
    # Для PostgreSQL используем raw SQL с корректным GROUP BY
    try:
        # PostgreSQL version - используем DATE() для конвертации
        registrations_query = text("""
            SELECT DATE(date_trunc('day', created_at)) as date, COUNT(id) as count
            FROM users
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY DATE(date_trunc('day', created_at))
            ORDER BY date
        """)
        registrations_result = await session.execute(
            registrations_query,
            {"start_date": start_date, "end_date": end_date}
        )
        registrations = {row.date: row.count for row in registrations_result}
    except Exception as e:
        # Fallback для SQLite
        registrations_query = select(
            func.strftime('%Y-%m-%d', User.created_at).label('date'),
            func.count(User.id).label('count')
        ).where(
            and_(User.created_at >= start_date, User.created_at <= end_date)
        ).group_by(func.strftime('%Y-%m-%d', User.created_at))
        registrations_result = await session.execute(registrations_query)
        registrations = {row.date: row.count for row in registrations_result}

    # Получаем конфиги по дням
    try:
        # PostgreSQL version
        configs_query = text("""
            SELECT DATE(date_trunc('day', created_at)) as date, COUNT(id) as count
            FROM config_history
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY DATE(date_trunc('day', created_at))
            ORDER BY date
        """)
        configs_result = await session.execute(
            configs_query,
            {"start_date": start_date, "end_date": end_date}
        )
        configs = {row.date: row.count for row in configs_result}
    except Exception as e:
        # Fallback для SQLite
        configs_query = select(
            func.strftime('%Y-%m-%d', ConfigHistory.created_at).label('date'),
            func.count(ConfigHistory.id).label('count')
        ).where(
            and_(ConfigHistory.created_at >= start_date, ConfigHistory.created_at <= end_date)
        ).group_by(func.strftime('%Y-%m-%d', ConfigHistory.created_at))
        configs_result = await session.execute(configs_query)
        configs = {row.date: row.count for row in configs_result}

    # Объединяем данные
    all_dates = set(registrations.keys()) | set(configs.keys())

    chart_data = []
    for date in sorted(all_dates):
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        chart_data.append(AdminStatsChartData(
            date=date_str,
            registrations=registrations.get(date, 0),
            configs_generated=configs.get(date, 0),
        ))

    return chart_data


# =============================================================================
# Global Settings
# =============================================================================

@router.get("/settings", response_model=List[GlobalSettingResponse])
async def get_global_settings(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение всех глобальных настроек.
    
    Настройки кэшируются в памяти на 60 секунд.
    """
    global _settings_cache, _settings_cache_timestamp
    import time
    
    current_time = time.time()
    
    # Проверка кэша
    if _settings_cache and (current_time - _settings_cache_timestamp) < CACHE_TTL_SECONDS:
        return list(_settings_cache.values())
    
    # Получаем из БД
    result = await session.execute(select(GlobalSetting).order_by(GlobalSetting.key))
    settings = result.scalars().all()
    
    # Обновляем кэш
    _settings_cache = {s.key: s for s in settings}
    _settings_cache_timestamp = current_time
    
    return [
        GlobalSettingResponse(
            key=s.key,
            value=s.value,
            updated_at=s.updated_at,
        )
        for s in settings
    ]


@router.patch("/settings/{setting_key}", response_model=GlobalSettingResponse)
async def update_global_setting(
    setting_key: str,
    data: GlobalSettingUpdate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Обновление глобальной настройки.

    - **setting_key**: Ключ настройки
    - **value**: Новое значение (JSON)

    Note:
        Кэш инвалидируется сразу после обновления для обеспечения консистентности.
    """
    global _settings_cache, _settings_cache_timestamp
    import time

    # Ищем настройку по ключу (не по id!)
    result = await session.execute(
        select(GlobalSetting).where(GlobalSetting.key == setting_key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        # Создаём новую
        setting = GlobalSetting(
            key=setting_key,
            value=data.value,
        )
        session.add(setting)
    else:
        # Обновляем
        setting.value = data.value
        setting.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(setting)

    # Инвалидация кэша (сразу после commit)
    _settings_cache[setting_key] = setting
    _settings_cache_timestamp = time.time()

    # Логирование через AuditLogService для консистентности
    audit_service = AuditLogService(session)
    await audit_service.log_settings_updated(
        admin_user_id=current_admin.id,
        admin_username=current_admin.username,
        setting_key=setting_key,
        setting_value=data.value,
        ip_address=None,
    )

    return GlobalSettingResponse(
        key=setting.key,
        value=setting.value,
        updated_at=setting.updated_at,
    )


# =============================================================================
# Maintenance Mode Management
# =============================================================================

@router.post("/maintenance/enable")
async def enable_maintenance_mode(
    request: Request,
    message: str = Query(default="Технические работы", max_length=500),
    estimated_end: Optional[str] = Query(default=None, max_length=100),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Включить режим обслуживания.
    
    - **message**: Сообщение для пользователей
    - **estimated_end**: Предполагаемое время окончания (ISO 8601)
    
    В режиме обслуживания:
    - Все запросы пользователей возвращают 503
    - Администраторы могут продолжать работу
    - Health check endpoints доступны всем
    """
    from services.maintenance_service import MaintenanceService
    
    # Инвалидируем кэш перед изменением
    MaintenanceService.invalidate_cache()
    
    success = await MaintenanceService.enable_maintenance(
        session=session,
        message=message,
        estimated_end=estimated_end,
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Не удалось включить режим обслуживания"
        )
    
    # Логирование через AuditLogService
    audit_service = AuditLogService(session)
    await audit_service.log_event(
        user_id=current_admin.id,
        username=current_admin.username,
        event_type="MAINTENANCE_ENABLED",
        details={
            "message": message,
            "estimated_end": estimated_end,
        },
        ip_address=request.client.host if request.client else None,
    )
    
    return {
        "status": "success",
        "message": "Режим обслуживания включён",
        "maintenance": {
            "enabled": True,
            "message": message,
            "estimated_end": estimated_end,
        }
    }


@router.post("/maintenance/disable")
async def disable_maintenance_mode(
    request: Request,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Выключить режим обслуживания.
    """
    from services.maintenance_service import MaintenanceService
    
    # Инвалидируем кэш перед изменением
    MaintenanceService.invalidate_cache()
    
    success = await MaintenanceService.disable_maintenance(session=session)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Не удалось выключить режим обслуживания"
        )
    
    # Логирование через AuditLogService
    audit_service = AuditLogService(session)
    await audit_service.log_event(
        user_id=current_admin.id,
        username=current_admin.username,
        event_type="MAINTENANCE_DISABLED",
        details={},
        ip_address=request.client.host if request.client else None,
    )
    
    return {
        "status": "success",
        "message": "Режим обслуживания выключен"
    }


@router.get("/maintenance/status")
async def get_maintenance_status(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получить текущий статус режима обслуживания.
    """
    from services.maintenance_service import MaintenanceService
    
    # Получаем актуальный статус из БД (не из кэша)
    maintenance_info = await MaintenanceService.get_maintenance_info(session)
    
    is_maintenance = False
    if maintenance_info and isinstance(maintenance_info, dict):
        is_maintenance = maintenance_info.get("enabled", False)
    
    return {
        "enabled": is_maintenance,
        "info": maintenance_info,
    }


# =============================================================================
# Helper Functions
# =============================================================================

async def _log_admin_action(
    session: AsyncSession,
    admin_user: User,
    event_type: str,
    details: dict,
    request: Optional[Request] = None,
):
    """
    Логирует действие администратора.

    Args:
        session: Сессия БД
        admin_user: Пользователь-администратор
        event_type: Тип события
        details: Детали события
        request: HTTP запрос (для получения IP)
    
    Note:
        Использует транзакцию для обеспечения консистентности.
        Если user_id не существует, лог всё равно сохраняется (user_id=NULL).
    """
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None
    
    try:
        log_entry = AdminLog(
            user_id=admin_user.id,
            event_type=event_type,
            details=details,
            ip_address=ip_address,
        )
        
        session.add(log_entry)
        await session.commit()
    except Exception as e:
        # Откат транзакции при ошибке
        await session.rollback()
        logger.error(f"Failed to log admin action: {e}")
        # Не пробрасываем ошибку дальше, чтобы не ломать основной запрос
