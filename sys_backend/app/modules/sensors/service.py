from supabase import Client

from app.core.database import execute
from app.core.security import generate_api_key, hash_api_key
from app.domain.errors import InvalidApiKeyError, SensorNotFoundError
from app.modules.sensors.schema import SensorCreate, SensorCreated, SensorOut


def create_sensor(db: Client, payload: SensorCreate) -> SensorCreated:
  api_key = generate_api_key()

  rows = execute(db.table("sensors").insert({**payload.model_dump(), "api_key_hash": hash_api_key(api_key)}))

  return SensorCreated.model_validate({**rows[0], "api_key": api_key})


def list_sensors(db: Client) -> list[SensorOut]:
  rows = execute(db.table("sensors").select("*").order("id"))

  return [SensorOut.model_validate(row) for row in rows]


def get_sensor(db: Client, sensor_id: int) -> SensorOut:
  rows = execute(db.table("sensors").select("*").eq("id", sensor_id).limit(1))

  if not rows:
    raise SensorNotFoundError()

  return SensorOut.model_validate(rows[0])


def authenticate_sensor(db: Client, api_key: str | None) -> SensorOut:
  if not api_key:
    raise InvalidApiKeyError()

  rows = execute(db.table("sensors").select("*").eq("api_key_hash", hash_api_key(api_key)).limit(1))

  if not rows:
    raise InvalidApiKeyError()

  return SensorOut.model_validate(rows[0])
