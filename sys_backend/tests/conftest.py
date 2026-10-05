from datetime import datetime, timezone
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.database import get_supabase
from main import app

ADMIN_KEY = "admin-test-key"

VALID_SENSOR = {
  "name": "Rua A",
  "install_height_cm": 20.0,
  "attention_cm": 2.0,
  "avoid_cm": 5.0,
  "blocked_cm": 8.0,
}


def _comparable(value: Any) -> Any:
  if isinstance(value, str):
    try:
      return datetime.fromisoformat(value)
    except ValueError:
      return value
  return value


class FakeResponse:
  def __init__(self, data: list[dict[str, Any]]) -> None:
    self.data = data


class FakeQuery:
  def __init__(self, db: "FakeSupabase", table: str) -> None:
    self.db = db
    self.table = table
    self.filters: list[Callable[[dict[str, Any]], bool]] = []
    self.orderings: list[tuple[str, bool]] = []
    self.limit_count: int | None = None
    self.payload: dict[str, Any] | None = None

  def select(self, *columns: str) -> "FakeQuery":
    return self

  def insert(self, payload: dict[str, Any]) -> "FakeQuery":
    self.payload = payload
    return self

  def eq(self, column: str, value: Any) -> "FakeQuery":
    self.filters.append(lambda row: row[column] == value)
    return self

  def gte(self, column: str, value: Any) -> "FakeQuery":
    self.filters.append(lambda row: _comparable(row[column]) >= _comparable(value))
    return self

  def order(self, column: str, desc: bool = False) -> "FakeQuery":
    self.orderings.append((column, desc))
    return self

  def limit(self, count: int) -> "FakeQuery":
    self.limit_count = count
    return self

  def execute(self) -> FakeResponse:
    if self.db.fail_with is not None:
      raise self.db.fail_with

    if self.payload is not None:
      return FakeResponse([self.db.insert(self.table, self.payload)])

    rows = [row for row in self.db.tables[self.table] if all(check(row) for check in self.filters)]
    for column, desc in reversed(self.orderings):
      rows.sort(key=lambda row: row[column], reverse=desc)
    if self.limit_count is not None:
      rows = rows[: self.limit_count]

    return FakeResponse([dict(row) for row in rows])


class FakeSupabase:
  def __init__(self) -> None:
    self.tables: dict[str, list[dict[str, Any]]] = {"sensors": [], "readings": []}
    self.next_id = {"sensors": 1, "readings": 1}
    self.now: datetime | None = None
    self.fail_with: Exception | None = None

  def table(self, name: str) -> FakeQuery:
    return FakeQuery(self, name)

  def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
    created_at = self.now or datetime.now(timezone.utc)
    row = {**payload, "id": self.next_id[table], "created_at": created_at.isoformat()}

    self.next_id[table] += 1
    self.tables[table].append(row)

    return dict(row)


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
  app.dependency_overrides[get_supabase] = lambda: db
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
