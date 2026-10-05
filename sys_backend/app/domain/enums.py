from enum import Enum


class RoadStatus(str, Enum):
  LIVRE = "livre"
  ATENCAO = "atencao"
  EVITAR = "evitar"
  BLOQUEADA = "bloqueada"
  SEM_SINAL = "sem_sinal"
