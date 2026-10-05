import httpx
import pytest

from app.core.security import hash_api_key

VALID_SENSOR = {
    "name": "Rua A",
    "install_height_cm": 20.0,
    "attention_cm": 2.0,
    "avoid_cm": 5.0,
    "blocked_cm": 8.0,
}


def test_create_sensor_returns_plain_key_once_and_stores_only_hash(client, admin_headers, db):
    response = client.post("/sensors", json=VALID_SENSOR, headers=admin_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Rua A"
    assert body["api_key"].startswith("ws_")
    assert "api_key_hash" not in body
    assert db.tables["sensors"][0]["api_key_hash"] == hash_api_key(body["api_key"])
    assert body["api_key"] not in str(db.tables["sensors"])


def test_create_sensor_without_admin_key_is_rejected(client, db):
    response = client.post("/sensors", json=VALID_SENSOR)

    assert response.status_code == 401
    assert response.json() == {"detail": "X-Admin-Key ausente ou inválida"}
    assert db.tables["sensors"] == []


def test_create_sensor_with_wrong_admin_key_is_rejected(client, db):
    response = client.post("/sensors", json=VALID_SENSOR, headers={"X-Admin-Key": "wrong"})

    assert response.status_code == 401
    assert db.tables["sensors"] == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"attention_cm": 5.0, "avoid_cm": 2.0},
        {"avoid_cm": 8.0, "blocked_cm": 8.0},
        {"blocked_cm": 20.0},
        {"blocked_cm": 25.0},
        {"install_height_cm": 0},
        {"name": "   "},
    ],
)
def test_create_sensor_rejects_invalid_configuration(client, admin_headers, db, overrides):
    response = client.post("/sensors", json={**VALID_SENSOR, **overrides}, headers=admin_headers)

    assert response.status_code == 422
    assert db.tables["sensors"] == []


def test_list_sensors_is_ordered_and_hides_keys(client, create_sensor):
    create_sensor(name="Rua A")
    create_sensor(name="Rua B")

    response = client.get("/sensors")

    assert response.status_code == 200
    assert [sensor["name"] for sensor in response.json()] == ["Rua A", "Rua B"]
    assert all("api_key" not in sensor and "api_key_hash" not in sensor for sensor in response.json())


def test_get_sensor_by_id(client, create_sensor):
    sensor = create_sensor()

    response = client.get(f"/sensors/{sensor['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == sensor["id"]


def test_get_unknown_sensor_returns_404(client):
    response = client.get("/sensors/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sensor não encontrado"}


def test_database_unavailable_returns_503(client, db):
    db.fail_with = httpx.ConnectError("offline")

    response = client.get("/sensors")

    assert response.status_code == 503
    assert response.json() == {"detail": "Banco de dados indisponível"}
