from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import crud, models
from app.utils import price_parser


def validate_azs_number(azs_number: int):
    """Проверяет, что номер АЗС находится в диапазоне 1-999"""
    if not (1 <= azs_number <= 999):
        raise HTTPException(
            status_code=422, detail="Номер АЗС должен быть в диапазоне от 1 до 999"
        )


def validate_column_number(azs_number: int, column_number: int, db: Session):
    """Проверяет, что номер колонки существует для указанной АЗС"""
    try:
        # Получаем кэшированные данные АЗС
        cached_data = (
            db.query(models.PriceCache)
            .filter(models.PriceCache.azs_number == azs_number)
            .first()
        )

        if not cached_data:
            # Если данных нет в кэше, получаем их через API
            settings = crud.get_settings(db)
            # Убедитесь, что здесь тоже передается db
            azs_data = price_parser.get_azs_data_with_discount(azs_number, settings, db)

            if "error" in azs_data:
                raise HTTPException(status_code=404, detail=azs_data["error"])

            num_columns = len(azs_data.get("fuel", []))
        else:
            # Используем кэшированные данные
            azs_data = cached_data.prices_data
            num_columns = len(azs_data.get("fuel", []))

        if not (1 <= column_number <= num_columns):
            raise HTTPException(
                status_code=422,
                detail=f"Номер колонки должен быть в диапазоне от 1 до {num_columns} для АЗС #{azs_number}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при проверке номера колонки: {str(e)}"
        )
