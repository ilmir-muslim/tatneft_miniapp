import requests
import json


def get_all_keys(data, parent_key=""):
    """Рекурсивно получает все ключи из JSON"""
    keys = []

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            keys.append(full_key)
            # Рекурсивно получаем ключи из вложенных структур
            keys.extend(get_all_keys(value, full_key))

    elif isinstance(data, list) and data:
        # Берем первый элемент массива для анализа структуры
        keys.extend(get_all_keys(data[0], f"{parent_key}[]"))

    return keys


def analyze_api_structure(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            all_keys = get_all_keys(data)
            return all_keys
    except Exception as e:
        return [f"Error: {e}"]


# Анализируем все эндпоинты
endpoints = {
    "fuel_types": "https://api.gs.tatneft.ru/api/v2/azs/fuel_types/",
    "azs_list": "https://api.gs.tatneft.ru/api/v2/azs/",
    "features": "https://api.gs.tatneft.ru/api/v2/azs/features/",
}

print("ПОЛНЫЙ СПИСОК ВСЕХ КЛЮЧЕЙ:")
print("=" * 60)

for name, url in endpoints.items():
    print(f"\n{name.upper()}: {url}")
    keys = analyze_api_structure(url)

    for key in keys:
        print(f"  {key}")
