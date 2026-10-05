from datetime import datetime, timedelta, timezone

import pytest


def post_reading(client, api_key, distance):
    return client.post("/readings", json={"distance_cm": distance}, headers={"X-API-Key": api_key})


def test_first_reading_is_classified_without_history(client, create_sensor):
    sensor = create_sensor()

    response = post_reading(client, sensor["api_key"], 14.2)

    assert response.status_code == 201
    body = response.json()
    assert body["sensor_id"] == sensor["id"]
    assert body["distance_cm"] == 14.2
    assert body["water_level_cm"] == 5.8
    assert body["status"] == "evitar"


def test_reading_is_smoothed_over_last_five_levels(client, create_sensor):
    sensor = create_sensor()
    for _ in range(5):
        post_reading(client, sensor["api_key"], 20.0)

    first_flood = post_reading(client, sensor["api_key"], 10.0).json()
    second_flood = post_reading(client, sensor["api_key"], 10.0).json()

    assert first_flood["water_level_cm"] == 2.0
    assert first_flood["status"] == "atencao"
    assert second_flood["water_level_cm"] == 4.0


def test_smoothing_ignores_other_sensors_history(client, create_sensor):
    dry = create_sensor(name="Rua A")
    flooded = create_sensor(name="Rua B")
    for _ in range(4):
        post_reading(client, dry["api_key"], 20.0)

    body = post_reading(client, flooded["api_key"], 10.0).json()

    assert body["sensor_id"] == flooded["id"]
    assert body["water_level_cm"] == 10.0
    assert body["status"] == "bloqueada"


def test_reading_slightly_beyond_installation_height_counts_as_dry(client, create_sensor):
    sensor = create_sensor()

    body = post_reading(client, sensor["api_key"], 22.0).json()

    assert body["water_level_cm"] == 0.0
    assert body["status"] == "livre"


@pytest.mark.parametrize("distance", [0.0, -3.0, 25.5])
def test_out_of_range_distance_is_rejected(client, create_sensor, db, distance):
    sensor = create_sensor()

    response = post_reading(client, sensor["api_key"], distance)

    assert response.status_code == 422
    assert response.json() == {"detail": "distance_cm deve ser maior que 0 e no máximo 25.0 cm"}
    assert db.tables["readings"] == []


@pytest.mark.parametrize(
    "raw_body",
    ['{"distance_cm": NaN}', '{"distance_cm": Infinity}', '{"distance_cm": "abc"}', "{}"],
)
def test_malformed_distance_is_rejected(client, create_sensor, db, raw_body):
    sensor = create_sensor()

    response = client.post(
        "/readings",
        content=raw_body,
        headers={"X-API-Key": sensor["api_key"], "Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert db.tables["readings"] == []


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "ws_invalida"}])
def test_reading_requires_valid_sensor_key(client, create_sensor, db, headers):
    create_sensor()

    response = client.post("/readings", json={"distance_cm": 10.0}, headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "X-API-Key ausente ou inválida"}
    assert db.tables["readings"] == []


def test_list_readings_is_chronological_and_filtered_by_sensor(client, create_sensor):
    first = create_sensor(name="Rua A")
    second = create_sensor(name="Rua B")
    post_reading(client, first["api_key"], 20.0)
    post_reading(client, second["api_key"], 15.0)
    post_reading(client, first["api_key"], 18.0)

    filtered = client.get("/readings", params={"sensor_id": first["id"]})
    unfiltered = client.get("/readings")

    assert filtered.status_code == 200
    assert [reading["distance_cm"] for reading in filtered.json()] == [20.0, 18.0]
    assert [reading["distance_cm"] for reading in unfiltered.json()] == [20.0, 15.0, 18.0]


def test_list_readings_keeps_most_recent_when_over_limit(client, create_sensor):
    sensor = create_sensor()
    for distance in [20.0, 19.0, 18.0, 17.0]:
        post_reading(client, sensor["api_key"], distance)

    response = client.get("/readings", params={"limit": 2})

    assert [reading["distance_cm"] for reading in response.json()] == [18.0, 17.0]


def test_list_readings_defaults_to_last_hour(client, create_sensor, db):
    sensor = create_sensor()
    db.now = datetime.now(timezone.utc) - timedelta(hours=2)
    post_reading(client, sensor["api_key"], 20.0)
    db.now = None
    post_reading(client, sensor["api_key"], 19.0)

    response = client.get("/readings")

    assert [reading["distance_cm"] for reading in response.json()] == [19.0]


@pytest.mark.parametrize("since", ["2026-10-05T18:10:00+00:00", "2026-10-05T18:10:00"])
def test_list_readings_respects_since_and_treats_naive_as_utc(client, create_sensor, db, since):
    sensor = create_sensor()
    base = datetime(2026, 10, 5, 18, 0, tzinfo=timezone.utc)
    for minutes, distance in [(0, 20.0), (10, 19.0), (20, 18.0)]:
        db.now = base + timedelta(minutes=minutes)
        post_reading(client, sensor["api_key"], distance)

    response = client.get("/readings", params={"since": since})

    assert [reading["distance_cm"] for reading in response.json()] == [19.0, 18.0]


def test_list_readings_for_unknown_sensor_returns_404(client):
    response = client.get("/readings", params={"sensor_id": 999})

    assert response.status_code == 404
    assert response.json() == {"detail": "Sensor não encontrado"}


@pytest.mark.parametrize("limit", [0, 1001])
def test_list_readings_rejects_invalid_limit(client, limit):
    assert client.get("/readings", params={"limit": limit}).status_code == 422
