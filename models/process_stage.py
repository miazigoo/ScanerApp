from pydantic import BaseModel


class ProcessStage(BaseModel):
    id: int
    name: str = "Undefined"
    sort_number: int = 0  # Добавляем поле для сортировки

    class Config:
        from_attributes = True