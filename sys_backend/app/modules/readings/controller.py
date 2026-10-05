from datetime import datetime

from fastapi import APIRouter, Depends, Query, Security
from supabase import Client

from app.core.config import Settings, get_settings
from app.core.database import get_supabase
from app.core.responses import error_responses
from app.core.security import sensor_key_header
from app.domain.errors import DatabaseUnavailableError, InvalidApiKeyError, InvalidReadingError, SensorNotFoundError
from app.modules.readings import service
from app.modules.readings.schema import ReadingIn, ReadingOut
from app.modules.sensors import service as sensor_service
from app.modules.sensors.schema import SensorOut

router = APIRouter(prefix="/readings", tags=["Readings"])


def get_authenticated_sensor(
    api_key: str | None = Security(sensor_key_header),
    db: Client = Depends(get_supabase),
) -> SensorOut:
    return sensor_service.authenticate_sensor(db, api_key)


@router.post(
    "",
    response_model=ReadingOut,
    status_code=201,
    summary="Recebe uma leitura do sensor",
    description="Endpoint chamado pelo ESP32. O sensor é identificado pela X-API-Key; a API calcula o nível da água, suaviza com média móvel e classifica a situação da via.",
    responses=error_responses(InvalidApiKeyError, InvalidReadingError, DatabaseUnavailableError),
)
def create_reading(
    payload: ReadingIn,
    sensor: SensorOut = Depends(get_authenticated_sensor),
    db: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
) -> ReadingOut:
    return service.create_reading(db, sensor, payload, settings)


@router.get(
    "",
    response_model=list[ReadingOut],
    summary="Histórico de leituras",
    description="Retorna leituras a partir de `since` em ordem cronológica crescente. Se houver mais leituras que `limit`, são mantidas as mais recentes.",
    responses=error_responses(SensorNotFoundError, DatabaseUnavailableError),
)
def list_readings(
    sensor_id: int | None = Query(default=None, description="Filtra por via"),
    since: datetime | None = Query(default=None, description="Início da janela em ISO 8601 (sem fuso = UTC). Padrão: última hora"),
    limit: int = Query(default=500, ge=1, le=1000, description="Quantidade máxima de leituras (teto do Supabase: 1000)"),
    db: Client = Depends(get_supabase),
) -> list[ReadingOut]:
    return service.list_readings(db, sensor_id, since, limit)
