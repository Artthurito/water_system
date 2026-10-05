import argparse
import random
import time
from collections.abc import Iterator

import httpx


def simulated_levels(peak_cm: float, steps: int) -> Iterator[float]:
  while True:
    for step in range(steps):
      yield peak_cm * step / steps
    for step in range(steps, 0, -1):
      yield peak_cm * step / steps


def main() -> None:
  parser = argparse.ArgumentParser(description="Simula um sensor de nível enviando leituras para a API")
  parser.add_argument("--api-key", required=True, help="Chave do sensor retornada por POST /sensors")
  parser.add_argument("--url", default="http://localhost:8000", help="URL base da API")
  parser.add_argument("--interval", type=float, default=5.0, help="Segundos entre leituras")
  parser.add_argument("--height", type=float, default=20.0, help="install_height_cm do sensor")
  parser.add_argument("--peak", type=float, default=10.0, help="Nível máximo de água simulado, em cm")
  parser.add_argument("--steps", type=int, default=20, help="Leituras para subir do zero ao pico")
  args = parser.parse_args()

  for level in simulated_levels(args.peak, args.steps):
    distance = round(max(0.1, args.height - level + random.uniform(-0.3, 0.3)), 2)

    try:
      response = httpx.post(
        f"{args.url}/readings",
        json={"distance_cm": distance},
        headers={"X-API-Key": args.api_key},
        timeout=5,
      )
      print(f"distance={distance:>6} cm -> {response.status_code} {response.text}")
    except httpx.HTTPError as error:
      print(f"distance={distance:>6} cm -> erro: {error}")

    time.sleep(args.interval)


if __name__ == "__main__":
  main()
