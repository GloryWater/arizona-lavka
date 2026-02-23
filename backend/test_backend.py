"""
Тестовый клиент для проверки backend.
"""

import httpx
import asyncio


async def test_backend():
    """Тестирует backend endpoints."""
    base_url = "http://127.0.0.1:8002"
    
    print("Тестирование backend...")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1. Health check (/)")
        try:
            response = await client.get(f"{base_url}/", timeout=5.0)
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.json()}")
        except Exception as e:
            print(f"   Ошибка: {e}")
        
        # Test 2: API Health check
        print("\n2. API Health check (/api/health)")
        try:
            response = await client.get(f"{base_url}/api/health", timeout=5.0)
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.json()}")
        except Exception as e:
            print(f"   Ошибка: {e}")
        
        # Test 3: Get servers
        print("\n3. Get servers (/api/marketplace/servers)")
        try:
            response = await client.get(f"{base_url}/api/marketplace/servers", timeout=10.0)
            print(f"   Статус: {response.status_code}")
            data = response.json()
            print(f"   Всего серверов: {data.get('total', 0)}")
        except Exception as e:
            print(f"   Ошибка: {e}")
        
        # Test 4: Get items
        print("\n4. Get items (/api/marketplace/items)")
        try:
            response = await client.get(f"{base_url}/api/marketplace/items", timeout=10.0)
            print(f"   Статус: {response.status_code}")
            data = response.json()
            print(f"   Всего предметов: {len(data)}")
        except Exception as e:
            print(f"   Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(test_backend())
