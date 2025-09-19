import os
import aiofiles
from fastapi import UploadFile, HTTPException
import uuid
import logging

logger = logging.getLogger(__name__)


class FileStorage:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Initialized FileStorage with directory: {upload_dir}")

    async def save_uploaded_file(self, file: UploadFile) -> str:
        # Разрешаем только определенные типы файлов
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/pdf",
        }

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Недопустимый тип файла. Разрешены только изображения и PDF.",
            )

        # Генерируем уникальное имя файла с сохранением расширения
        file_extension = file.filename.split(".")[-1]
        new_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(self.upload_dir, new_filename)

        logger.info(f"Saving file: {file.filename} as {new_filename}")

        # Сохраняем файл асинхронно
        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                content = await file.read()
                await buffer.write(content)

            logger.info(f"File saved successfully: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}"
            )


file_storage = FileStorage()
