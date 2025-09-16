import os
from fastapi import UploadFile
import uuid


class FileStorage:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def save_uploaded_file(self, file: UploadFile) -> str:
        file_extension = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(self.upload_dir, filename)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return file_path


file_storage = FileStorage()
