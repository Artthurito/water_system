import threading
from datetime import datetime, timezone
from typing import Any, Callable


def _comparable(value: Any) -> Any:
  if isinstance(value, str):
    try:
      return datetime.fromisoformat(value)
    except ValueError:
      return value
  return value


class CacheResponse:
  def __init__(self, data: list[dict[str, Any]]) -> None:
    self.data = data


class CacheQuery:
  def __init__(self, db: "CacheDatabase", table: str) -> None:
    self.db = db
    self.table = table
    self.filters: list[Callable[[dict[str, Any]], bool]] = []
    self.orderings: list[tuple[str, bool]] = []
    self.limit_count: int | None = None
    self.payload: dict[str, Any] | None = None

  def select(self, *columns: str) -> "CacheQuery":
    return self

  def insert(self, payload: dict[str, Any]) -> "CacheQuery":
    self.payload = payload
    return self

  def eq(self, column: str, value: Any) -> "CacheQuery":
    self.filters.append(lambda row: row[column] == value)
    return self

  def gte(self, column: str, value: Any) -> "CacheQuery":
    self.filters.append(lambda row: _comparable(row[column]) >= _comparable(value))
    return self

  def order(self, column: str, desc: bool = False) -> "CacheQuery":
    self.orderings.append((column, desc))
    return self

  def limit(self, count: int) -> "CacheQuery":
    self.limit_count = count
    return self

  def execute(self) -> CacheResponse:
    if self.payload is not None:
      return CacheResponse([self.db.insert(self.table, self.payload)])

    with self.db.lock:
      rows = [dict(row) for row in self.db.tables[self.table] if all(check(row) for check in self.filters)]

    for column, desc in reversed(self.orderings):
      rows.sort(key=lambda row: row[column], reverse=desc)
    if self.limit_count is not None:
      rows = rows[: self.limit_count]

    return CacheResponse(rows)


class CacheDatabase:
  def __init__(self) -> None:
    self.tables: dict[str, list[dict[str, Any]]] = {"sensors": [], "readings": []}
    self.next_id = {"sensors": 1, "readings": 1}
    self.lock = threading.Lock()

  def table(self, name: str) -> CacheQuery:
    return CacheQuery(self, name)

  def current_time(self) -> datetime:
    return datetime.now(timezone.utc)

  def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
    with self.lock:
      row = {**payload, "id": self.next_id[table], "created_at": self.current_time().isoformat()}

      self.next_id[table] += 1
      self.tables[table].append(row)

    return dict(row)
