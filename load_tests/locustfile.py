"""
Locust load tests for Arizona Lavka Marketplace.

Запуск:
    uv run locust -f load_tests/locustfile.py --host https://lavka.glorysyntax.live

Веб-интерфейс откроется на: http://localhost:8089
"""

import random
import json
from locust import HttpUser, task, between, events
from datetime import datetime


class MarketplaceUser(HttpUser):
    """
    Симуляция обычного пользователя marketplace.
    
    Сценарии:
    - Просмотр главной страницы
    - Просмотр списка лавок
    - Просмотр конкретной лавки
    - Генерация конфига (самая тяжёлая операция)
    """
    
    # Пауза между запросами (1-3 секунды)
    wait_time = between(1, 3)
    
    # Тестовые данные
    test_servers = [0, 1, 2, 5, 10]  # VC, Phoenix, Tucson, etc.
    test_modes = ["SELL", "BUY"]
    
    def on_start(self):
        """Выполняется при старте каждого пользователя."""
        # Можно добавить логин если нужно тестировать авторизованные запросы
        pass
    
    @task(3)
    def view_homepage(self):
        """Просмотр главной страницы (лёгкий запрос)."""
        self.client.get("/", name="Homepage")
    
    @task(5)
    def view_lavkas(self):
        """Просмотр списка лавок (средний запрос)."""
        server_id = random.choice(self.test_servers)
        self.client.get(
            f"/api/marketplace/lavkas?server_id={server_id}",
            name="Lavkas List"
        )
    
    @task(4)
    def view_lavka_detail(self):
        """Просмотр конкретной лавки (средний запрос)."""
        # Используем тестовый lavka_uid
        lavka_uid = f"test_{random.randint(1, 100)}"
        server_id = random.choice(self.test_servers)
        self.client.get(
            f"/api/marketplace/lavka/{lavka_uid}?server_id={server_id}",
            name="Lavka Detail"
        )
    
    @task(2)
    def view_offers(self):
        """Просмотр офферов (средний запрос)."""
        server_id = random.choice(self.test_servers)
        self.client.get(
            f"/api/marketplace/offers?server_id={server_id}",
            name="Offers List"
        )
    
    @task(1)
    def generate_config(self):
        """
        Генерация конфига (самая тяжёлая операция).
        
        Внимание: Эта операция нагружает сервер больше всего.
        Используйте меньший вес (task(1)) для реалистичного сценария.
        """
        server_id = random.choice(self.test_servers)
        mode = random.choice(self.test_modes)
        
        payload = {
            "server_id": server_id,
            "mode": mode,
            "percentage": random.randint(-10, 10),
            "save_to_history": False,  # Не сохраняем в историю для теста
            "min_liquidity": 0.0,
        }
        
        with self.client.post(
            "/api/config/generate",
            json=payload,
            name="Config Generate",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Ожидаемо для неавторизованных
                response.success()
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
            else:
                response.success()  # Другие коды считаем успехом для теста


class AdminUser(HttpUser):
    """
    Симуляция администратора.
    
    Запускайте отдельно с меньшим количеством пользователей.
    """
    
    wait_time = between(2, 5)
    
    # Тестовые данные админа (замените на реальные для теста)
    admin_username = "admin"
    admin_password = "admin_password"
    
    def on_start(self):
        """Логин при старте."""
        # Раскомментируйте если нужен реальный логин
        # response = self.client.post("/api/auth/login", json={
        #     "username": self.admin_username,
        #     "password": self.admin_password,
        # })
        # if response.status_code == 200:
        #     self.token = response.json().get("access_token")
        #     self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        pass
    
    @task(2)
    def view_admin_dashboard(self):
        """Просмотр админ-дашборда."""
        self.client.get("/admin", name="Admin Dashboard")
    
    @task(3)
    def view_admin_stats(self):
        """Просмотр статистики."""
        self.client.get("/api/admin/stats/summary", name="Admin Stats")
    
    @task(2)
    def view_admin_users(self):
        """Просмотр пользователей."""
        self.client.get("/api/admin/users?page=1&limit=50", name="Admin Users")
    
    @task(1)
    def view_admin_logs(self):
        """Просмотр логов."""
        self.client.get("/api/admin/logs?page=1&limit=20", name="Admin Logs")


class APIOnlyUser(HttpUser):
    """
    Только API запросы (без фронтенда).
    
    Для тестирования чистой нагрузки на бэкенд.
    """
    
    wait_time = between(0.5, 2)
    
    test_servers = [0, 1, 2]
    
    @task(5)
    def api_lavkas(self):
        """API: Список лавок."""
        server_id = random.choice(self.test_servers)
        self.client.get(f"/api/marketplace/lavkas?server_id={server_id}")
    
    @task(3)
    def api_offers(self):
        """API: Офферы."""
        server_id = random.choice(self.test_servers)
        self.client.get(f"/api/marketplace/offers?server_id={server_id}")
    
    @task(1)
    def api_health(self):
        """API: Health check."""
        self.client.get("/api/health", name="Health Check")


# Обработчики событий для логирования
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Логирование начала теста."""
    print(f"\n{'='*60}")
    print(f"Нагрузочное тестирование начато: {datetime.now()}")
    print(f"Целевой хост: {environment.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Логирование окончания теста."""
    print(f"\n{'='*60}")
    print(f"Нагрузочное тестирование завершено: {datetime.now()}")
    print(f"{'='*60}\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Логирование медленных запросов."""
    if response_time > 2000:  # > 2 секунд
        print(f"[WARN] Slow request: {name} - {response_time}ms")
