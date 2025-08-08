from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Barcode(BaseModel):
    id: Optional[int] = None
    code: str = ""
    order: int = 0
    user_id: int = 0
    stage: int = 0
    is_good: bool = False
    created_at: Optional[datetime] = None
    is_sent: bool = False
    error_count: int = 0

    class Config:
        from_attributes = True


class BarcodeImportSchema(BaseModel):
    code: str
    created_at: datetime
    user_id: int
    order: int
    stage: int
    is_good: bool