import logging
from functools import lru_cache
from typing import Any

import httpx
from postgrest.exceptions import APIError
from supabase import Client, ClientOptions, create_client

from app.core.cache import CacheDatabase
from app.core.config import get_settings
from app.domain.errors import DatabaseUnavailableError

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase() -> Client:
  settings = get_settings()
  options = ClientOptions(postgrest_client_timeout=settings.supabase_timeout_seconds)
  return create_client(settings.supabase_url, settings.supabase_service_key, options=options)


@lru_cache
def get_database() -> Client | CacheDatabase:
  if get_settings().db_mode == "cache":
    logger.warning("DB_MODE=cache: os dados ficam em memória e são perdidos ao reiniciar a API")
    return CacheDatabase()

  return get_supabase()


def execute(query: Any) -> list[dict[str, Any]]:
  try:
    return query.execute().data
  except (APIError, httpx.HTTPError) as error:
    logger.warning("Falha ao acessar o Supabase: %r", error)
    raise DatabaseUnavailableError() from error
