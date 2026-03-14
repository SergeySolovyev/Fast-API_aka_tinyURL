def test_root_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "BTFL" in response.text


def test_api_info(client):
    response = client.get("/api")

    assert response.status_code == 200
    assert response.json() == {
        "message": "BTFL link API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
