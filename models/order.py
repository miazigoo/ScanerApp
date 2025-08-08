from typing import Optional, Union

from pydantic import BaseModel
from models.process_type import ProcessType

class Order(BaseModel):
    id: int
    name: str = ""
    sort_name: int = 0
    process_type_id: int = 0
    process_type: Optional[Union[int, ProcessType]] = None  # Может быть как ID, так и объектом

    class Config:
        from_attributes = True

    def get_process_type_id(self) -> int:
        """Возвращает корректный ID типа процесса"""
        if isinstance(self.process_type, int):
            return self.process_type
        elif isinstance(self.process_type, ProcessType):
            return self.process_type.id
        return self.process_type_id