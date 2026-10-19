from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  db_mode: Literal["supabase", "cache"] = "supabase"
  supabase_url: str = ""
  supabase_service_key: str = ""
  admin_api_key: str
  supabase_timeout_seconds: float = Field(default=5.0, gt=0)
  distance_tolerance_cm: float = Field(default=5.0, ge=0)
  smoothing_window: int = Field(default=5, ge=1)
  stale_after_seconds: int = Field(default=120, gt=0)

  @model_validator(mode="after")
  def check_supabase_credentials(self) -> "Settings":
    if self.db_mode == "supabase" and not (self.supabase_url and self.supabase_service_key):
      raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórias quando DB_MODE=supabase")
    return self


@lru_cache
def get_settings() -> Settings:
  return Settings()
