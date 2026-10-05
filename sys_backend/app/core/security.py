import hashlib
import secrets

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings
from app.domain.errors import InvalidAdminKeyError

API_KEY_PREFIX = "ws_"

sensor_key_header = APIKeyHeader(
  name="X-API-Key",
  scheme_name="SensorKey",
  auto_error=False,
  description="Chave do sensor gravada no ESP32",
)
admin_key_header = APIKeyHeader(
  name="X-Admin-Key",
  scheme_name="AdminKey",
  auto_error=False,
  description="Chave de administração definida em ADMIN_API_KEY",
)


def generate_api_key() -> str:
  return API_KEY_PREFIX + secrets.token_urlsafe(24)


def hash_api_key(api_key: str) -> str:
  return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def require_admin(
  admin_key: str | None = Security(admin_key_header),
  settings: Settings = Depends(get_settings),
) -> None:
  if not admin_key or not secrets.compare_digest(admin_key.encode("utf-8"), settings.admin_api_key.encode("utf-8")):
    raise InvalidAdminKeyError()
