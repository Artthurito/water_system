from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import DomainError
from app.modules.analysis.controller import router as analysis_router
from app.modules.readings.controller import router as readings_router
from app.modules.sensors.controller import router as sensors_router

app = FastAPI(
  title="Water System API",
  version="1.0.0",
  description="API de monitoramento de alagamentos urbanos: recebe leituras dos sensores, classifica a situação das vias e expõe o histórico.",
)

app.include_router(sensors_router)
app.include_router(readings_router)
app.include_router(analysis_router)


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
  return JSONResponse(status_code=error.status_code, content={"detail": error.message})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
  errors = [{key: value for key, value in item.items() if key != "input"} for item in error.errors()]
  return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})
