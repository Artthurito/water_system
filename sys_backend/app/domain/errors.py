class DomainError(Exception):
  status_code = 400
  message = "Requisição inválida"

  def __init__(self, message: str | None = None) -> None:
    self.message = message or type(self).message
    super().__init__(self.message)


class InvalidApiKeyError(DomainError):
  status_code = 401
  message = "X-API-Key ausente ou inválida"


class InvalidAdminKeyError(DomainError):
  status_code = 401
  message = "X-Admin-Key ausente ou inválida"


class SensorNotFoundError(DomainError):
  status_code = 404
  message = "Sensor não encontrado"


class InvalidReadingError(DomainError):
  status_code = 422
  message = "Leitura fora da faixa válida"


class DatabaseUnavailableError(DomainError):
  status_code = 503
  message = "Banco de dados indisponível"
