from pydantic import BaseModel

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    page_count: int
    chunk_count: int
    message: str