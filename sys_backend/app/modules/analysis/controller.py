from fastapi import APIRouter, Depends
from supabase import Client

from app.core.config import Settings, get_settings
from app.core.database import get_database
from app.core.responses import error_responses
from app.domain.errors import DatabaseUnavailableError
from app.modules.analysis import service
from app.modules.analysis.schema import StatusOverview

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get(
  "/status",
  response_model=StatusOverview,
  summary="Situação atual das vias",
  description="Retorna a última situação de cada via, ordenada da melhor para a pior, com as vias sem sinal no final e o caminho recomendado.",
  responses=error_responses(DatabaseUnavailableError),
)
def get_status(db: Client = Depends(get_database), settings: Settings = Depends(get_settings)) -> StatusOverview:
  return service.get_status_overview(db, settings)
