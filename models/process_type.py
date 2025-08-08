from pydantic import BaseModel
from typing import Optional, List
from models.process_stage import ProcessStage

class ProcessType(BaseModel):
    id: int
    name: str = "Undefined"
    stages: List[ProcessStage] = []
