from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.cache import CacheDatabase, CacheQuery, CacheResponse
from app.core.config import Settings, get_settings
from app.core.database import get_database
from main import app

ADMIN_KEY = "admin-test-key"

VALID_SENSOR = {
  "name": "Rua A",
  "install_height_cm": 20.0,
  "attention_cm": 2.0,
  "avoid_cm": 5.0,
  "blocked_cm": 8.0,
}


class FakeQuery(CacheQuery):
  def execute(self) -> CacheResponse:
    if self.db.fail_with is not None:
      raise self.db.fail_with

    return super().execute()


class FakeSupabase(CacheDatabase):
  def __init__(self) -> None:
    super().__init__()
    self.now: datetime | None = None
    self.fail_with: Exception | None = None

  def table(self, name: str) -> FakeQuery:
    return FakeQuery(self, name)

  def current_time(self) -> datetime:
    return self.now or super().current_time()


@pytest.fixture
def settings() -> Settings:
  return Settings(
    _env_file=None,
    supabase_url="http://supabase.test",
    supabase_service_key="service-test-key",
    admin_api_key=ADMIN_KEY,
  )


@pytest.fixture
def db() -> FakeSupabase:
  return FakeSupabase()


@pytest.fixture
def client(db: FakeSupabase, settings: Settings):
  app.dependency_overrides[get_database] = lambda: db
  app.dependency_overrides[get_settings] = lambda: settings

  with TestClient(app) as test_client:
    yield test_client

  app.dependency_overrides.clear()


@pytest.fixture
def admin_headers() -> dict[str, str]:
  return {"X-Admin-Key": ADMIN_KEY}


@pytest.fixture
def create_sensor(client: TestClient, admin_headers: dict[str, str]):
  def _create(**overrides: Any) -> dict[str, Any]:
    response = client.post("/sensors", json={**VALID_SENSOR, **overrides}, headers=admin_headers)
    assert response.status_code == 201, response.text
    return response.json()

  return _create
