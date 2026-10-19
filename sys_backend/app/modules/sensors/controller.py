from fastapi import APIRouter, Depends
from supabase import Client

from app.core.database import get_database
from app.core.responses import error_responses
from app.core.security import require_admin
from app.domain.errors import DatabaseUnavailableError, InvalidAdminKeyError, SensorNotFoundError
from app.modules.sensors import service
from app.modules.sensors.schema import SensorCreate, SensorCreated, SensorOut

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post(
  "",
  response_model=SensorCreated,
  status_code=201,
  summary="Cadastra uma via",
  description="Cria o sensor de uma via e gera a chave que deve ser gravada no ESP32. A chave em texto puro só é exibida nesta resposta.",
  responses=error_responses(InvalidAdminKeyError, DatabaseUnavailableError),
  dependencies=[Depends(require_admin)],
)
def create_sensor(payload: SensorCreate, db: Client = Depends(get_database)) -> SensorCreated:
  return service.create_sensor(db, payload)


@router.get(
  "",
  response_model=list[SensorOut],
  summary="Lista as vias",
  description="Retorna todas as vias cadastradas, ordenadas por id, com os limites de cada situação.",
  responses=error_responses(DatabaseUnavailableError),
)
def list_sensors(db: Client = Depends(get_database)) -> list[SensorOut]:
  return service.list_sensors(db)


@router.get(
  "/{sensor_id}",
  response_model=SensorOut,
  summary="Detalha uma via",
  description="Retorna os dados de uma via cadastrada.",
  responses=error_responses(SensorNotFoundError, DatabaseUnavailableError),
)
def get_sensor(sensor_id: int, db: Client = Depends(get_database)) -> SensorOut:
  return service.get_sensor(db, sensor_id)
