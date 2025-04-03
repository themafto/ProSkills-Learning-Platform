from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    """Schema for file information returned from S3"""

    key: str
    size: int
    last_modified: datetime
    etag: str


class FileUploadResponse(BaseModel):
    """Schema for successful file upload response"""

    message: str
    file_key: str


class FileDeleteResponse(BaseModel):
    """Schema for successful file deletion response"""

    message: str
