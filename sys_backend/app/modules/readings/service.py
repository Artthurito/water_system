from datetime import datetime, timedelta, timezone

from supabase import Client

from app.core.config import Settings
from app.core.database import execute
from app.domain.errors import InvalidReadingError
from app.modules.analysis.utils import classify, is_valid_distance, moving_average, water_level
from app.modules.readings.schema import ReadingIn, ReadingOut
from app.modules.sensors import service as sensor_service
from app.modules.sensors.schema import SensorOut

DEFAULT_WINDOW = timedelta(hours=1)


def create_reading(db: Client, sensor: SensorOut, payload: ReadingIn, settings: Settings) -> ReadingOut:
    max_distance = sensor.install_height_cm + settings.distance_tolerance_cm
    if not is_valid_distance(payload.distance_cm, sensor.install_height_cm, settings.distance_tolerance_cm):
        raise InvalidReadingError(f"distance_cm deve ser maior que 0 e no máximo {max_distance} cm")

    previous_distances = _latest_distances(db, sensor.id, settings.smoothing_window - 1)

    distances = [payload.distance_cm, *previous_distances]
    level = round(moving_average([water_level(sensor.install_height_cm, distance) for distance in distances]), 2)
    status = classify(level, sensor.attention_cm, sensor.avoid_cm, sensor.blocked_cm)

    rows = execute(
        db.table("readings").insert(
            {
                "sensor_id": sensor.id,
                "distance_cm": payload.distance_cm,
                "water_level_cm": level,
                "status": status.value,
            }
        )
    )

    return ReadingOut.model_validate(rows[0])


def list_readings(db: Client, sensor_id: int | None, since: datetime | None, limit: int) -> list[ReadingOut]:
    if sensor_id is not None:
        sensor_service.get_sensor(db, sensor_id)

    since = since or datetime.now(timezone.utc) - DEFAULT_WINDOW
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    since_utc = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    query = db.table("readings").select("*").gte("created_at", since_utc)
    if sensor_id is not None:
        query = query.eq("sensor_id", sensor_id)
    rows = execute(query.order("id", desc=True).limit(limit))

    return [ReadingOut.model_validate(row) for row in reversed(rows)]


def latest_reading(db: Client, sensor_id: int) -> ReadingOut | None:
    rows = execute(db.table("readings").select("*").eq("sensor_id", sensor_id).order("id", desc=True).limit(1))

    return ReadingOut.model_validate(rows[0]) if rows else None


def _latest_distances(db: Client, sensor_id: int, count: int) -> list[float]:
    if count <= 0:
        return []

    rows = execute(
        db.table("readings").select("distance_cm").eq("sensor_id", sensor_id).order("id", desc=True).limit(count)
    )

    return [row["distance_cm"] for row in rows]
