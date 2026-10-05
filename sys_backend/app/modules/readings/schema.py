from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import RoadStatus


class ReadingIn(BaseModel):
    distance_cm: float = Field(
        allow_inf_nan=False,
        description="Distância medida pelo laser até a superfície, em cm",
        examples=[14.2],
    )


class ReadingOut(BaseModel):
    id: int
    sensor_id: int
    distance_cm: float
    water_level_cm: float
    status: RoadStatus
    created_at: datetime
