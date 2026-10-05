from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import RoadStatus


class SensorStatus(BaseModel):
  sensor_id: int
  name: str
  water_level_cm: float | None
  status: RoadStatus
  last_reading_at: datetime | None


class StatusOverview(BaseModel):
  generated_at: datetime
  recommended_sensor_id: int | None
  sensors: list[SensorStatus]
