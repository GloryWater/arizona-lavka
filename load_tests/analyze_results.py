"""
Анализ результатов нагрузочного тестирования.

Использование:
    uv run python load_tests/analyze_results.py --file results/test_20260301_120000_stats.csv
"""

import argparse
import csv
import json
from pathlib import Path
from datetime import datetime


def parse_csv(filepath: str) -> list[dict]:
    """Чтение CSV файла с результатами."""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def analyze_stats(filepath: str) -> dict:
    """Анализ файла stats.csv."""
    data = parse_csv(filepath)
    
    if not data:
        return {"error": "No data"}
    
    # Последняя строка содержит итоговую статистику
    final = data[-1]
    
    return {
        "total_requests": int(final.get("Request Count", 0)),
        "num_users": int(final.get("User Count", 0)),
        "response_time_avg": float(final.get("Response Time Avg", 0)),
        "response_time_min": float(final.get("Response Time Min", 0)),
        "response_time_max": float(final.get("Response Time Max", 0)),
        "response_time_median": float(final.get("Response Time Median", 0)),
        "response_time_p95": float(final.get("Response Time 95%ile", 0)),
        "requests_per_sec": float(final.get("Requests/s", 0)),
        "failures": int(final.get("Failure Count", 0)),
        "failure_rate": float(final.get("Failure Ratio", 0)),
    }


def analyze_requests(filepath: str) -> dict:
    """Анализ файла requests.csv по типам запросов."""
    data = parse_csv(filepath)
    
    analysis = {}
    for row in data:
        name = row.get("Name", "Unknown")
        if name == "Aggregated":
            continue
        
        analysis[name] = {
            "requests": int(row.get("Request Count", 0)),
            "avg_time": float(row.get("Response Time Avg", 0)),
            "p95_time": float(row.get("Response Time 95%ile", 0)),
            "failures": int(row.get("Failure Count", 0)),
            "failure_rate": float(row.get("Failure Ratio", 0)),
        }
    
    return analysis


def print_report(stats: dict, requests: dict) -> None:
    """Вывод отчёта в консоль."""
    print("\n" + "=" * 60)
    print("ОТЧЁТ ПО НАГРУЗОЧНОМУ ТЕСТИРОВАНИЮ")
    print("=" * 60)
    print(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Запросов всего:     {stats['total_requests']:,}")
    print(f"  Пользователей:      {stats['num_users']}")
    print(f"  Запросов/сек:       {stats['requests_per_sec']:.1f}")
    
    print("\n⏱️ ВРЕМЯ ОТВЕТА:")
    print(f"  Среднее:            {stats['response_time_avg']:.0f} ms")
    print(f"  Минимум:            {stats['response_time_min']:.0f} ms")
    print(f"  Максимум:           {stats['response_time_max']:.0f} ms")
    print(f"  Медиана:            {stats['response_time_median']:.0f} ms")
    print(f"  95-й перцентиль:    {stats['response_time_p95']:.0f} ms")
    
    print("\n❌ ОШИБКИ:")
    print(f"  Всего ошибок:       {stats['failures']}")
    print(f"  Процент ошибок:     {stats['failure_rate']:.2%}")
    
    print("\n📈 ПО ЗАПРОСАМ:")
    for name, data in sorted(requests.items(), key=lambda x: x[1]['requests'], reverse=True):
        status = "✅" if data['failure_rate'] < 0.01 else "⚠️" if data['failure_rate'] < 0.05 else "❌"
        print(f"\n  {status} {name}:")
        print(f"      Запросов:  {data['requests']:,}")
        print(f"      Среднее:   {data['avg_time']:.0f} ms")
        print(f"      95-й %:    {data['p95_time']:.0f} ms")
        print(f"      Ошибки:    {data['failure_rate']:.2%}")
    
    # Оценка
    print("\n" + "=" * 60)
    print("ОЦЕНКА РЕЗУЛЬТАТОВ:")
    print("=" * 60)
    
    score = 100
    
    if stats['response_time_p95'] > 5000:
        score -= 30
        print("  ❌ Критично: 95-й перцентиль > 5 секунд")
    elif stats['response_time_p95'] > 2000:
        score -= 15
        print("  ⚠️  Проблема: 95-й перцентиль > 2 секунд")
    elif stats['response_time_p95'] > 1000:
        score -= 5
        print("  ⚠️  Внимание: 95-й перцентиль > 1 секунды")
    else:
        print("  ✅ Отлично: 95-й перцентиль < 1 секунды")
    
    if stats['failure_rate'] > 0.05:
        score -= 30
        print("  ❌ Критично: Ошибки > 5%")
    elif stats['failure_rate'] > 0.01:
        score -= 15
        print("  ⚠️  Проблема: Ошибки > 1%")
    else:
        print("  ✅ Отлично: Ошибки < 1%")
    
    if stats['requests_per_sec'] < 50:
        score -= 10
        print("  ⚠️  Низкая пропускная способность: < 50 req/s")
    elif stats['requests_per_sec'] > 200:
        print("  ✅ Отличная пропускная способность: > 200 req/s")
    
    print("\n" + "=" * 60)
    print(f"ИТОГОВАЯ ОЦЕНКА: {score}/100")
    
    if score >= 80:
        print("СТАТУС: ✅ Сервер готов к нагрузке")
    elif score >= 60:
        print("СТАТУС: ⚠️  Требуются улучшения")
    else:
        print("СТАТУС: ❌ Сервер не готов к нагрузке")
    
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Анализ результатов нагрузочного тестирования')
    parser.add_argument('--file', type=str, required=True, help='Путь к stats.csv')
    parser.add_argument('--requests-file', type=str, help='Путь к requests.csv (опционально)')
    parser.add_argument('--output', type=str, help='Сохранить отчёт в JSON')
    
    args = parser.parse_args()
    
    stats = analyze_stats(args.file)
    
    requests_file = args.requests_file or args.file.replace('_stats.csv', '_requests.csv')
    requests = {}
    if Path(requests_file).exists():
        requests = analyze_requests(requests_file)
    
    print_report(stats, requests)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({"stats": stats, "requests": requests}, f, indent=2)
        print(f"📄 Отчёт сохранён: {args.output}")


if __name__ == '__main__':
    main()
