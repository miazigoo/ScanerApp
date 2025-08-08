from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: Optional[int] = None
    username: str = ""
    password: str = ""
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    permissions: List[str] = []
    is_authenticated: bool = False
    is_staff: bool = False
    is_superuser: bool = False

    class Config:
        from_attributes = True
