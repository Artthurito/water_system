import logging

import httpx
import pytest
from postgrest.exceptions import APIError

from pydantic import ValidationError

from app.core.cache import CacheDatabase
from app.core.config import Settings
from app.core.database import execute, get_database, get_supabase
from app.domain.errors import DatabaseUnavailableError


class StubQuery:
  def __init__(self, data=None, error=None):
    self.data = data
    self.error = error

  def execute(self):
    if self.error is not None:
      raise self.error
    return self


def test_execute_returns_response_data():
  assert execute(StubQuery(data=[{"id": 1}])) == [{"id": 1}]


@pytest.mark.parametrize(
  "error",
  [
    httpx.ConnectError("offline"),
    APIError({"message": "boom", "code": "500", "hint": None, "details": None}),
  ],
)
def test_execute_maps_driver_errors_to_database_unavailable(error):
  with pytest.raises(DatabaseUnavailableError):
    execute(StubQuery(error=error))


def test_execute_logs_the_driver_error(caplog):
  with caplog.at_level(logging.WARNING, logger="app.core.database"):
    with pytest.raises(DatabaseUnavailableError):
      execute(StubQuery(error=httpx.ConnectError("offline")))

  assert "offline" in caplog.text


def test_supabase_client_fails_fast_instead_of_default_120s(settings, monkeypatch):
  monkeypatch.setattr("app.core.database.get_settings", lambda: settings)
  get_supabase.cache_clear()

  client = get_supabase()

  assert client.options.postgrest_client_timeout == 5
  get_supabase.cache_clear()


def test_cache_mode_uses_a_single_in_memory_database(monkeypatch):
  settings = Settings(_env_file=None, db_mode="cache", admin_api_key="admin")
  monkeypatch.setattr("app.core.database.get_settings", lambda: settings)
  get_database.cache_clear()

  database = get_database()

  assert isinstance(database, CacheDatabase)
  assert get_database() is database
  get_database.cache_clear()


def test_supabase_mode_uses_the_supabase_client(settings, monkeypatch):
  monkeypatch.setattr("app.core.database.get_settings", lambda: settings)
  get_supabase.cache_clear()
  get_database.cache_clear()

  assert get_database() is get_supabase()
  get_supabase.cache_clear()
  get_database.cache_clear()


def test_supabase_mode_requires_credentials():
  with pytest.raises(ValidationError, match="SUPABASE_URL e SUPABASE_SERVICE_KEY"):
    Settings(_env_file=None, db_mode="supabase", admin_api_key="admin")


def test_cache_mode_does_not_require_supabase_credentials():
  settings = Settings(_env_file=None, db_mode="cache", admin_api_key="admin")

  assert settings.supabase_url == ""


def test_invalid_db_mode_is_rejected():
  with pytest.raises(ValidationError):
    Settings(_env_file=None, db_mode="mongo", admin_api_key="admin")
