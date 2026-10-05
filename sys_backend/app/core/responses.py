from typing import Any

from pydantic import BaseModel

from app.domain.errors import DomainError


class ErrorResponse(BaseModel):
  detail: str | list[dict[str, Any]]


def error_responses(*errors: type[DomainError]) -> dict[int | str, dict[str, Any]]:
  return {error.status_code: {"model": ErrorResponse, "description": error.message} for error in errors}
