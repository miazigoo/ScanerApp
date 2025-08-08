from pydantic import BaseModel


class Session(BaseModel):
    id: int = 1
    username: str
    password: str

    class Config:
        from_attributes = True