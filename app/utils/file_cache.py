import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class FileCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_timeout = timedelta(minutes=15)

    def _get_file_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if (
                datetime.now() - datetime.fromisoformat(data["updated_at"])
                > self.cache_timeout
            ):
                return None
            return data["data"]
        except Exception as e:
            logger.error(f"Error reading cache file {file_path}: {e}")
            return None

    def set(self, key: str, data: Any):
        file_path = self._get_file_path(key)
        try:
            cache_data = {"data": data, "updated_at": datetime.now().isoformat()}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error writing cache file {file_path}: {e}")

    def delete(self, key: str):
        """Удаляет данные по ключу"""
        file_path = self._get_file_path(key)
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache file {file_path}: {e}")
            return False


    def get_last_updated(self, key: str) -> Optional[datetime]:
        """Получает время последнего обновления кэша"""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return datetime.fromisoformat(data["updated_at"])
        except Exception as e:
            logger.error(f"Error reading cache file {file_path}: {e}")
            return None


    def is_cache_expired(self, key: str, hours: int = 12) -> bool:
        """Проверяет, устарел ли кэш (старше указанного количества часов)"""
        last_updated = self.get_last_updated(key)
        if not last_updated:
            return True

        return datetime.now() - last_updated > timedelta(hours=hours)


# Глобальный экземпляр кэша
file_cache = FileCache()
