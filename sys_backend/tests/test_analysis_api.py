from datetime import datetime, timedelta, timezone


def post_reading(client, api_key, distance):
    response = client.post("/readings", json={"distance_cm": distance}, headers={"X-API-Key": api_key})
    assert response.status_code == 201, response.text


def test_status_without_sensors(client):
    response = client.get("/analysis/status")

    assert response.status_code == 200
    assert response.json()["sensors"] == []
    assert response.json()["recommended_sensor_id"] is None


def test_sensor_without_readings_has_no_signal(client, create_sensor):
    sensor = create_sensor()

    body = client.get("/analysis/status").json()

    assert body["sensors"] == [
        {
            "sensor_id": sensor["id"],
            "name": "Rua A",
            "water_level_cm": None,
            "status": "sem_sinal",
            "last_reading_at": None,
        }
    ]
    assert body["recommended_sensor_id"] is None


def test_stale_sensor_has_no_signal_and_goes_last(client, create_sensor, db):
    stale = create_sensor(name="Rua A")
    fresh = create_sensor(name="Rua B")
    db.now = datetime.now(timezone.utc) - timedelta(minutes=10)
    post_reading(client, stale["api_key"], 20.0)
    db.now = None
    post_reading(client, fresh["api_key"], 16.0)

    body = client.get("/analysis/status").json()

    assert [item["sensor_id"] for item in body["sensors"]] == [fresh["id"], stale["id"]]
    assert body["sensors"][1]["status"] == "sem_sinal"
    assert body["sensors"][1]["water_level_cm"] is None
    assert body["sensors"][1]["last_reading_at"] is not None
    assert body["recommended_sensor_id"] == fresh["id"]


def test_roads_are_ranked_by_level_and_driest_is_recommended(client, create_sensor):
    flooded = create_sensor(name="Rua A")
    dry = create_sensor(name="Rua B")
    wet = create_sensor(name="Rua C")
    post_reading(client, flooded["api_key"], 10.0)
    post_reading(client, dry["api_key"], 20.0)
    post_reading(client, wet["api_key"], 14.0)

    body = client.get("/analysis/status").json()

    assert [(item["sensor_id"], item["status"]) for item in body["sensors"]] == [
        (dry["id"], "livre"),
        (wet["id"], "evitar"),
        (flooded["id"], "bloqueada"),
    ]
    assert body["recommended_sensor_id"] == dry["id"]


def test_recommendation_skips_blocked_road_even_with_lower_level(client, create_sensor):
    sensitive = create_sensor(name="Rua A", attention_cm=1.0, avoid_cm=2.0, blocked_cm=3.0)
    regular = create_sensor(name="Rua B")
    post_reading(client, sensitive["api_key"], 16.0)
    post_reading(client, regular["api_key"], 14.0)

    body = client.get("/analysis/status").json()

    assert body["sensors"][0]["sensor_id"] == sensitive["id"]
    assert body["sensors"][0]["status"] == "bloqueada"
    assert body["recommended_sensor_id"] == regular["id"]


def test_no_recommendation_when_every_road_is_blocked(client, create_sensor):
    sensor = create_sensor()
    post_reading(client, sensor["api_key"], 10.0)

    assert client.get("/analysis/status").json()["recommended_sensor_id"] is None
