def test_expected_routes_are_published(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert set(paths) == {"/sensors", "/sensors/{sensor_id}", "/readings", "/analysis/status"}


def test_every_operation_has_tag_summary_and_description(client):
    paths = client.get("/openapi.json").json()["paths"]
    operations = [operation for path in paths.values() for operation in path.values()]

    for operation in operations:
        assert operation.get("tags")
        assert operation.get("summary")
        assert operation.get("description")


def test_security_headers_are_exposed_in_swagger(client):
    schemes = client.get("/openapi.json").json()["components"]["securitySchemes"]

    assert {scheme["name"] for scheme in schemes.values()} == {"X-API-Key", "X-Admin-Key"}
