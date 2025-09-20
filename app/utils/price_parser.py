import requests
from datetime import datetime, timedelta
from app.utils.file_cache import file_cache


class PriceParser:
    def __init__(self):
        self.base_url = "https://api.gs.tatneft.ru/api/v2/azs"
        self.cache_timeout = timedelta(minutes=15)
        self.fuel_types_cache = None
        self.azs_list_cache = None
        self.cache_expiration = None

    def get_azs_list(self, use_cache_on_error: bool = True):
        """Получает и кэширует список всех АЗС с fallback на кэш при ошибках"""
        current_time = datetime.now()

        # Проверяем актуальность кэша в памяти
        if (
            self.azs_list_cache is not None
            and self.cache_expiration is not None
            and current_time < self.cache_expiration
        ):
            return self.azs_list_cache

        # Проверяем файловый кэш
        cached_data = file_cache.get("azs_list")
        if cached_data:
            self.azs_list_cache = cached_data
            self.cache_expiration = datetime.now() + self.cache_timeout
            return self.azs_list_cache

        try:
            # Запрос к API
            response = requests.get(f"{self.base_url}/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.azs_list_cache = data.get("data", [])
                self.cache_expiration = current_time + self.cache_timeout
                file_cache.set("azs_list", self.azs_list_cache)
                return self.azs_list_cache
            else:
                return []
        except Exception as e:
            print(f"Ошибка при получении списка АЗС: {e}")
            return []

    def get_fuel_types(self, use_cache_on_error: bool = True):
        """Получает и кэширует справочник типов топлива с fallback на кэш"""
        if self.fuel_types_cache is not None:
            return self.fuel_types_cache

        # Проверяем файловый кэш
        cached_data = file_cache.get("fuel_types")
        if cached_data:
            self.fuel_types_cache = cached_data
            return self.fuel_types_cache

        try:
            # Запрос к API
            response = requests.get(f"{self.base_url}/fuel_types/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.fuel_types_cache = {
                    item["id"]: {
                        "name": item["title"],
                        "color": item.get("color", ""),
                        "filter_group": item.get("filter_group_title", ""),
                    }
                    for item in data.get("data", {}).get("items", [])
                }
                file_cache.set("fuel_types", self.fuel_types_cache)
                return self.fuel_types_cache
            else:
                return {}
        except Exception as e:
            print(f"Ошибка при получении справочника топлива: {e}")
            return {}

    def get_azs_data_with_discount(self, azs_number: int, settings):
        """Получает данные АЗС с применением скидки с fallback на кэш при ошибках"""
        # Проверяем файловый кэш
        cached_data = file_cache.get(f"azs_{azs_number}")
        use_cached_data = False

        # Если есть актуальный кэш, используем его
        if cached_data:
            azs_data = cached_data
        else:
            try:
                # Получаем список АЗС
                azs_list = self.get_azs_list(use_cache_on_error=True)
                if not azs_list:
                    return {"error": "Не удалось загрузить список АЗС"}

                # Ищем нужную АЗС
                target_azs = None
                for azs in azs_list:
                    if azs.get("number") == azs_number:
                        target_azs = azs
                        break

                if not target_azs:
                    return {"error": f"АЗС с номером {azs_number} не найдена"}

                azs_data = {
                    "azs_number": target_azs.get("number"),
                    "address": target_azs.get("address"),
                    "region": target_azs.get("region"),
                    "fuel": target_azs.get("fuel", []),
                    "actualization_date": target_azs.get("actualization_date"),
                }

                # Сохраняем в кэш
                file_cache.set(f"azs_{azs_number}", azs_data)

            except Exception as e:
                print(f"Ошибка при обновлении данных АЗС {azs_number}: {e}")
                # Если при обновлении произошла ошибка, используем кэшированные данные
                if cached_data:
                    print(f"Используются кэшированные данные для АЗС {azs_number}")
                    azs_data = cached_data
                    use_cached_data = True
                else:
                    return {
                        "error": f"Не удалось загрузить данные для АЗС {azs_number}"
                    }

        # Получаем справочник топлива
        fuel_types = self.get_fuel_types(use_cache_on_error=True)

        # Обрабатываем данные о топливе
        fuel_data = []
        for fuel in azs_data.get("fuel", []):
            fuel_type_id = fuel.get("fuel_type_id")
            price = fuel.get("price")
            discount_price = fuel.get("discount_price")

            # Используем оригинальную цену если нет скидки
            final_price = discount_price if discount_price is not None else price

            # Применяем скидку из настроек
            discounted_price = final_price
            if final_price is not None and settings:
                if settings.discount_type == "percent":
                    discounted_price = final_price * (1 - settings.discount_value / 100)
                elif settings.discount_type == "fixed":
                    discounted_price = max(0, final_price - settings.discount_value)

            # Получаем информацию о типе топлива
            fuel_info = fuel_types.get(fuel_type_id, {})

            fuel_data.append(
                {
                    "fuel_type_id": fuel_type_id,
                    "name": fuel_info.get("name", f"Топливо {fuel_type_id}"),
                    "price": price,  # Оригинальная цена
                    "discount_price": discounted_price,  # Цена со скидкой
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
        }

        return result
