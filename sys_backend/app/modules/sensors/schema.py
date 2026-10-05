from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

SensorName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class SensorCreate(BaseModel):
    name: SensorName = Field(description="Nome da via", examples=["Rua A"])
    install_height_cm: float = Field(gt=0, allow_inf_nan=False, description="Distância do sensor até o chão seco", examples=[20.0])
    attention_cm: float = Field(gt=0, allow_inf_nan=False, description="Nível a partir do qual a via fica em atenção", examples=[2.0])
    avoid_cm: float = Field(gt=0, allow_inf_nan=False, description="Nível a partir do qual a via deve ser evitada", examples=[5.0])
    blocked_cm: float = Field(gt=0, allow_inf_nan=False, description="Nível a partir do qual a via fica bloqueada", examples=[8.0])

    @model_validator(mode="after")
    def check_thresholds(self) -> "SensorCreate":
        if not self.attention_cm < self.avoid_cm < self.blocked_cm:
            raise ValueError("Os limites devem respeitar attention_cm < avoid_cm < blocked_cm")
        if self.blocked_cm >= self.install_height_cm:
            raise ValueError("blocked_cm deve ser menor que install_height_cm")
        return self


class SensorOut(BaseModel):
    id: int
    name: str
    install_height_cm: float
    attention_cm: float
    avoid_cm: float
    blocked_cm: float
    created_at: datetime


class SensorCreated(SensorOut):
    api_key: str = Field(description="Chave do sensor em texto puro. Exibida somente nesta resposta.")
