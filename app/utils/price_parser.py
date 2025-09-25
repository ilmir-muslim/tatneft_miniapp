from typing import Optional
from pathlib import Path
import requests
from datetime import datetime, timedelta
from app.utils.file_cache import file_cache


class PriceParser:
    def __init__(self):
        self.base_url = "https://api.gs.tatneft.ru/api/v2/azs"
        self.cache_timeout = timedelta(minutes=15)
        self.long_cache_timeout = timedelta(hours=12)
        self.fuel_types_cache = None
        self.azs_list_cache = None
        self.cache_expiration = None
        self.cache_dir = Path("cache") 
        self.cache_dir.mkdir(exist_ok=True)

    def get_azs_list(
        self, use_cache_on_error: bool = True, force_refresh: bool = False
    ):
        """Получает и кэширует список всех АЗС с проверкой времени обновления"""
        current_time = datetime.now()

        # Проверяем, нужно ли принудительное обновление из-за устаревшего кэша
        if not force_refresh:
            cache_age = file_cache.get_last_updated("azs_list")
            if cache_age and (current_time - cache_age) > self.long_cache_timeout:
                print("Кэш списка АЗС устарел (старше 12 часов), обновляем...")
                force_refresh = True

        # Если не принудительное обновление, проверяем актуальность кэша в памяти
        if not force_refresh and (
            self.azs_list_cache is not None
            and self.cache_expiration is not None
            and current_time < self.cache_expiration
        ):
            return self.azs_list_cache

        # Проверяем файловый кэш (если не требуется принудительное обновление)
        if not force_refresh:
            cached_data = file_cache.get("azs_list")
            if cached_data:
                self.azs_list_cache = cached_data
                self.cache_expiration = datetime.now() + self.cache_timeout
                return self.azs_list_cache

        try:
            # Запрос к API для обновления данных
            print("Обновление данных списка АЗС с сервера...")
            response = requests.get(f"{self.base_url}/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.azs_list_cache = data.get("data", [])
                self.cache_expiration = current_time + self.cache_timeout
                file_cache.set("azs_list", self.azs_list_cache)
                print("Данные списка АЗС успешно обновлены")
                return self.azs_list_cache
            else:
                # Если API вернуло ошибку, используем кэш если разрешено
                if use_cache_on_error and not force_refresh:
                    cached_data = file_cache.get("azs_list")
                    if cached_data:
                        print("Используем кэшированные данные из-за ошибки API")
                        self.azs_list_cache = cached_data
                        return self.azs_list_cache
                return []
        except Exception as e:
            print(f"Ошибка при получении списка АЗС: {e}")
            # Используем кэш при ошибке, если разрешено и не требуется принудительное обновление
            if use_cache_on_error and not force_refresh:
                cached_data = file_cache.get("azs_list")
                if cached_data:
                    print("Используем кэшированные данные из-за ошибки соединения")
                    self.azs_list_cache = cached_data
                    return self.azs_list_cache
            return []

    def get_fuel_types(
        self, use_cache_on_error: bool = True, force_refresh: bool = False
    ):
        """Получает и кэширует справочник типов топлива с проверкой времени обновления"""
        current_time = datetime.now()

        # Проверяем, нужно ли принудительное обновление из-за устаревшего кэша
        if not force_refresh:
            cache_age = file_cache.get_last_updated("fuel_types")
            if cache_age and (current_time - cache_age) > self.long_cache_timeout:
                print("Кэш типов топлива устарел (старше 12 часов), обновляем...")
                force_refresh = True

        if not force_refresh and self.fuel_types_cache is not None:
            return self.fuel_types_cache

        # Проверяем файловый кэш (если не требуется принудительное обновление)
        if not force_refresh:
            cached_data = file_cache.get("fuel_types")
            if cached_data:
                # Извлекаем данные из правильной структуры кэша
                fuel_data = cached_data.get("data", {})
                # Конвертируем строковые ключи в числа
                converted_data = {}
                for key, value in fuel_data.items():
                    try:
                        num_key = int(key)
                        converted_data[num_key] = value
                    except ValueError:
                        converted_data[key] = value
                self.fuel_types_cache = converted_data
                return self.fuel_types_cache

        try:
            # Запрос к API для обновления данных
            print("Обновление данных типов топлива с сервера...")
            response = requests.get(f"{self.base_url}/fuel_types/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.fuel_types_cache = {}
                for item in data.get("data", {}).get("items", []):
                    fuel_id = item["id"]
                    self.fuel_types_cache[fuel_id] = {
                        "name": item["title"],
                        "color": item.get("color", ""),
                        "filter_group": item.get("filter_group_title", ""),
                    }
                # Сохраняем в правильном формате
                file_cache.set("fuel_types", {"data": self.fuel_types_cache})
                print("Данные типов топлива успешно обновлены")
                return self.fuel_types_cache
            else:
                # Если API вернуло ошибку, используем кэш если разрешено
                if use_cache_on_error and not force_refresh:
                    cached_data = file_cache.get("fuel_types")
                    if cached_data:
                        print(
                            "Используем кэшированные данные типов топлива из-за ошибки API"
                        )
                        fuel_data = cached_data.get("data", {})
                        converted_data = {}
                        for key, value in fuel_data.items():
                            try:
                                num_key = int(key)
                                converted_data[num_key] = value
                            except ValueError:
                                converted_data[key] = value
                        self.fuel_types_cache = converted_data
                        return self.fuel_types_cache
                return {}
        except Exception as e:
            print(f"Ошибка при получении справочника топлива: {e}")
            # Используем кэш при ошибке, если разрешено и не требуется принудительное обновление
            if use_cache_on_error and not force_refresh:
                cached_data = file_cache.get("fuel_types")
                if cached_data:
                    print(
                        "Используем кэшированные данные типов топлива из-за ошибки соединения"
                    )
                    fuel_data = cached_data.get("data", {})
                    converted_data = {}
                    for key, value in fuel_data.items():
                        try:
                            num_key = int(key)
                            converted_data[num_key] = value
                        except ValueError:
                            converted_data[key] = value
                    self.fuel_types_cache = converted_data
                    return self.fuel_types_cache
            return {}

    def get_azs_data_with_discount(
        self,
        azs_number: int,
        settings,
        azs_id: Optional[int] = None,
        force_refresh: bool = False,
    ):
        """Получает данные конкретной АЗС с применением скидки и проверкой времени обновления"""
        # Формируем ключ кэша только если указан конкретный azs_id
        cache_key = f"azs_{azs_number}_{azs_id}" if azs_id else None

        # Проверяем, нужно ли принудительное обновление из-за устаревшего кэша
        if cache_key and not force_refresh:
            cache_age = file_cache.get_last_updated(cache_key)
            if cache_age and (datetime.now() - cache_age) > self.long_cache_timeout:
                print(f"Кэш АЗС {azs_number} (ID: {azs_id}) устарел, обновляем...")
                force_refresh = True

        cached_data = (
            file_cache.get(cache_key) if cache_key and not force_refresh else None
        )

        print(
            f"Поиск АЗС: номер={azs_number}, ID={azs_id}, ключ_кэша={cache_key}, force_refresh={force_refresh}"
        )

        # Если есть актуальный кэш для конкретной АЗС, используем его
        if cached_data and not force_refresh:
            print(f"Используются кэшированные данные для ключа: {cache_key}")
            azs_data = cached_data
        else:
            try:
                # Получаем список АЗС (может также обновиться, если устарел)
                azs_list = self.get_azs_list(
                    use_cache_on_error=True, force_refresh=force_refresh
                )
                if not azs_list:
                    return {"error": "Не удалось загрузить список АЗС"}

                # Ищем нужную АЗС с учетом ID
                target_azs = None
                for azs in azs_list:
                    if azs.get("number") == azs_number:
                        # Если указан azs_id, проверяем точное соответствие
                        if azs_id is not None:
                            if azs.get("id") == azs_id:
                                target_azs = azs
                                break
                        else:
                            # Если azs_id не указан, берем первую попавшуюся АЗС
                            target_azs = azs
                            break

                if not target_azs:
                    return {
                        "error": f"АЗС с номером {azs_number} и ID {azs_id} не найдена"
                    }

                print(
                    f"Найдена АЗС: ID={target_azs.get('id')}, адрес={target_azs.get('address')}"
                )

                azs_data = {
                    "azs_number": target_azs.get("number"),
                    "address": target_azs.get("address"),
                    "region": target_azs.get("region"),
                    "fuel": target_azs.get("fuel", []),
                    "actualization_date": target_azs.get("actualization_date"),
                    "id": target_azs.get("id"),
                }

                # Сохраняем в кэш ТОЛЬКО если указан конкретный azs_id
                if cache_key:
                    file_cache.set(cache_key, azs_data)
                    print(f"Данные АЗС сохранены в кэш с ключом: {cache_key}")

            except Exception as e:
                print(f"Ошибка при обновлении данных АЗС {azs_number}: {e}")
                # Если при обновлении произошла ошибка, используем кэшированные данные
                if cached_data:
                    print(
                        f"Используются кэшированные данные для АЗС {azs_number} (ID: {azs_id})"
                    )
                    azs_data = cached_data
                else:
                    return {
                        "error": f"Не удалось загрузить данные для АЗС {azs_number}"
                    }

        # Получаем типы топлива (может также обновиться, если устарел)
        fuel_types = self.get_fuel_types(
            use_cache_on_error=True, force_refresh=force_refresh
        )
        fuel_data = []

        for fuel in azs_data.get("fuel", []):
            fuel_type_id = fuel.get("fuel_type_id")
            price = fuel.get("price")
            discount_price = fuel.get("discount_price")

            final_price = discount_price if discount_price is not None else price
            discounted_price = final_price

            if final_price is not None and settings:
                if settings.discount_type == "percent":
                    discounted_price = final_price * (1 - settings.discount_value / 100)
                elif settings.discount_type == "fixed":
                    discounted_price = max(0, final_price - settings.discount_value)

            fuel_info = fuel_types.get(fuel_type_id, {})

            fuel_data.append(
                {
                    "fuel_type_id": fuel_type_id,
                    "name": fuel_info.get("name", f"Топливо {fuel_type_id}"),
                    "price": price,
                    "discount_price": discounted_price,
                    "currency_code": fuel.get("currency_code", "rub"),
                    "updated": fuel.get("updated"),
                    "color": fuel_info.get("color", ""),
                    "filter_group": fuel_info.get("filter_group", ""),
                }
            )

        result = {
            "azs_number": azs_data.get("azs_number"),
            "address": azs_data.get("address"),
            "region": azs_data.get("region"),
            "fuel": fuel_data,
            "actualization_date": azs_data.get("actualization_date"),
            "id": azs_data.get("id"),
        }

        return result

    def force_refresh_all_cache(self):
        """Принудительное обновление всех кэшей"""
        print("Принудительное обновление всех кэшей...")

        # Очищаем кэш в памяти
        self.azs_list_cache = None
        self.fuel_types_cache = None
        self.cache_expiration = None

        # Получаем данные с принудительным обновлением
        self.get_azs_list(force_refresh=True)
        self.get_fuel_types(force_refresh=True)

        print("Все кэши успешно обновлены")

    def clear_azs_cache(self, azs_number: int, azs_id: Optional[int] = None):
        """Очищает кэш для конкретной АЗС через FileCache"""
        if azs_id:
            # Очищаем кэш только для конкретной АЗС
            cache_key = f"azs_{azs_number}_{azs_id}"
            file_cache.delete(cache_key)
            print(f"Кэш очищен для АЗС {azs_number} (ID: {azs_id})")
        else:
            # Если azs_id не указан, находим все АЗС с этим номером и очищаем их кэш
            azs_list = self.get_azs_list(use_cache_on_error=True)
            if azs_list:
                for azs in azs_list:
                    if azs.get("number") == azs_number:
                        azs_id = azs.get("id")
                        cache_key = f"azs_{azs_number}_{azs_id}"
                        file_cache.delete(cache_key)
                        print(f"Кэш очищен для АЗС {azs_number} (ID: {azs_id})")

    def clear_all_cache(self):
        """Очищает весь кэш АЗС"""
        try:
            # Очищаем кэш в памяти
            self.azs_list_cache = None
            self.fuel_types_cache = None
            self.cache_expiration = None

            # Очищаем файловый кэш через file_cache
            file_cache_files = ["azs_list", "fuel_types"]

            # Добавляем все возможные ключи azs_*
            import os

            if os.path.exists("cache"):
                for file in os.listdir("cache"):
                    if file.startswith("azs_") and file.endswith(".json"):
                        cache_key = file.replace(".json", "")
                        file_cache_files.append(cache_key)

            # Удаляем каждый файл кэша
            for key in file_cache_files:
                file_path = Path("cache") / f"{key}.json"
                if file_path.exists():
                    file_path.unlink()

            print("Полная очистка кэша АЗС выполнена")
        except Exception as e:
            print(f"Ошибка при полной очистке кэша: {e}")
