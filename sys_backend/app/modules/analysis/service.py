from datetime import datetime, timezone

from supabase import Client

from app.core.config import Settings
from app.domain.enums import RoadStatus
from app.modules.analysis.schema import SensorStatus, StatusOverview
from app.modules.analysis.utils import is_stale
from app.modules.readings import service as reading_service
from app.modules.sensors import service as sensor_service
from app.modules.sensors.schema import SensorOut


def get_status_overview(db: Client, settings: Settings) -> StatusOverview:
  now = datetime.now(timezone.utc)
  sensors = sensor_service.list_sensors(db)

  statuses = [_sensor_status(db, sensor, now, settings.stale_after_seconds) for sensor in sensors]

  online = sorted(
    (item for item in statuses if item.status != RoadStatus.SEM_SINAL),
    key=lambda item: item.water_level_cm,
  )
  offline = [item for item in statuses if item.status == RoadStatus.SEM_SINAL]
  recommended = next((item.sensor_id for item in online if item.status != RoadStatus.BLOQUEADA), None)

  return StatusOverview(generated_at=now, recommended_sensor_id=recommended, sensors=online + offline)


def _sensor_status(db: Client, sensor: SensorOut, now: datetime, stale_after_seconds: int) -> SensorStatus:
  reading = reading_service.latest_reading(db, sensor.id)

  if reading is None:
    return SensorStatus(
      sensor_id=sensor.id,
      name=sensor.name,
      water_level_cm=None,
      status=RoadStatus.SEM_SINAL,
      last_reading_at=None,
    )

  if is_stale(reading.created_at, now, stale_after_seconds):
    return SensorStatus(
      sensor_id=sensor.id,
      name=sensor.name,
      water_level_cm=None,
      status=RoadStatus.SEM_SINAL,
      last_reading_at=reading.created_at,
    )

  return SensorStatus(
    sensor_id=sensor.id,
    name=sensor.name,
    water_level_cm=reading.water_level_cm,
    status=reading.status,
    last_reading_at=reading.created_at,
  )
