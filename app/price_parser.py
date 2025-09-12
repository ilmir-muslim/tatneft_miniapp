import requests
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from models import PriceCache



class PriceParser:
    def __init__(self):
        self.base_url = "https://api.gs.tatneft.ru/api/v2/azs"
        self.cache_timeout = timedelta(minutes=15)
        self.fuel_types_cache = None
        self.azs_cache = None

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
                    item["id"]: item["title"]
                    for item in data.get("data", {}).get("items", [])
                }
                return self.fuel_types_cache
            else:
                return {}
        except Exception as e:
            print(f"Ошибка при получении справочника топлива: {e}")
            return {}

    def get_azs_list(self):
        """Получает и кэширует список всех АЗС"""
        if self.azs_cache is not None:
            return self.azs_cache

        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.azs_cache = data.get("data", [])
                return self.azs_cache
            else:
                return []
        except Exception as e:
            print(f"Ошибка при получении списка АЗС: {e}")
            return []

    def parse_prices(self, azs_number: int) -> dict:
        """Получает цены на топливо для указанной АЗС через API"""
        try:
            # Получаем справочник типов топлива
            fuel_types = self.get_fuel_types()
            if not fuel_types:
                return {"error": "Не удалось загрузить справочник топлива"}

            # Получаем список всех АЗС
            azs_list = self.get_azs_list()
            if not azs_list:
                return {"error": "Не удалось загрузить список АЗС"}

            # Ищем нужную АЗС по номеру
            azs_data = None
            for azs in azs_list:
                if azs.get("number") == azs_number:
                    azs_data = azs
                    break

            if not azs_data:
                return {"error": f"АЗС с номером {azs_number} не найдена"}

            # Извлекаем цены на топливо
            prices = {}
            for fuel in azs_data.get("fuel", []):
                fuel_type_id = fuel.get("fuel_type_id")
                price = fuel.get("price")
                discount_price = fuel.get("discount_price")

                if fuel_type_id in fuel_types and price is not None:
                    fuel_name = fuel_types[fuel_type_id]
                    # Используем discount_price если доступен, иначе обычную цену
                    prices[fuel_name] = (
                        discount_price if discount_price is not None else price
                    )

            return prices

        except requests.RequestException as e:
            return {"error": f"Ошибка при запросе к API: {str(e)}"}
        except Exception as e:
            return {"error": f"Неожиданная ошибка: {str(e)}"}

    def get_cached_prices(self, db: Session, azs_number: int):
        """Получает закэшированные цены из базы данных"""
        cache = (
            db.query(PriceCache)
            .filter(
                PriceCache.azs_number == azs_number,
                PriceCache.updated_at >= datetime.now() - self.cache_timeout,
            )
            .first()
        )

        if cache:
            return json.loads(cache.prices_data)
        return None

    def cache_prices(self, db: Session, azs_number: int, prices: dict):
        """Сохраняет цены в кэш базы данных"""
        # Удаляем старые записи для этой АЗС
        db.query(PriceCache).filter(
            PriceCache.azs_number == azs_number
        ).delete()

        # Сохраняем новые данные
        cache = PriceCache(
            azs_number=azs_number,
            prices_data=json.dumps(prices),
            updated_at=datetime.now(),
        )

        db.add(cache)
        db.commit()
        return cache

    def get_prices(self, db: Session, azs_number: int):
        """Основной метод для получения цен (с кэшированием)"""
        # Проверяем кэш
        cached_prices = self.get_cached_prices(db, azs_number)
        if cached_prices:
            return cached_prices

        # Если в кэше нет данных, запрашиваем через API
        prices = self.parse_prices(azs_number)

        # Если запрос успешен, сохраняем в кэш
        if "error" not in prices:
            self.cache_prices(db, azs_number, prices)

        return prices
