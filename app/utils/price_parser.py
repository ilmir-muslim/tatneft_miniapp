import requests
from datetime import datetime, timedelta


class PriceParser:
    def __init__(self):
        self.base_url = "https://api.gs.tatneft.ru/api/v2/azs"
        self.cache_timeout = timedelta(minutes=15)
        self.fuel_types_cache = None
        self.azs_list_cache = None
        self.cache_expiration = None

    def get_azs_list(self):
        """Получает и кэширует список всех АЗС"""
        current_time = datetime.now()

        # Проверяем, актуален ли кэш
        if (
            self.azs_list_cache is not None
            and self.cache_expiration is not None
            and current_time < self.cache_expiration
        ):
            return self.azs_list_cache

        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.azs_list_cache = data.get("data", [])
                self.cache_expiration = current_time + self.cache_timeout
                return self.azs_list_cache
            else:
                return []
        except Exception as e:
            print(f"Ошибка при получении списка АЗС: {e}")
            return []

    def get_fuel_types(self):
        """Получает и кэширует справочник типов топлива"""
        if self.fuel_types_cache is not None:
            return self.fuel_types_cache

        try:
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
                return self.fuel_types_cache
            else:
                return {}
        except Exception as e:
            print(f"Ошибка при получении справочника топлива: {e}")
            return {}


    def get_azs_data_with_discount(self, azs_number: int, settings):
        """Получает данные АЗС с применением скидки"""
        # Получаем список АЗС
        azs_list = self.get_azs_list()
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

        # Получаем справочник топлива
        fuel_types = self.get_fuel_types()

        # Обрабатываем данные о топливе
        fuel_data = []
        for fuel in target_azs.get("fuel", []):
            fuel_type_id = fuel.get("fuel_type_id")
            price = fuel.get("price")
            discount_price = fuel.get("discount_price")

            # Используем оригинальную цену если нет скидки
            final_price = discount_price if discount_price is not None else price

            # Применяем скидку из настроек только если цена существует
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

        print(f"Original price: {price}, Discounted price: {discounted_price}")
        print(f"Settings: {settings.discount_type}, {settings.discount_value}")

        return {
            "azs_number": target_azs.get("number"),
            "address": target_azs.get("address"),
            "region": target_azs.get("region"),
            "fuel": fuel_data,
            "actualization_date": target_azs.get("actualization_date"),
        }
