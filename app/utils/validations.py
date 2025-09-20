from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import crud
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
        # Получаем настройки через crud с передачей сессии
        settings = crud.get_settings(db)
        azs_data = price_parser.get_azs_data_with_discount(azs_number, settings)

        if "error" in azs_data:
            raise HTTPException(status_code=404, detail=azs_data["error"])

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
