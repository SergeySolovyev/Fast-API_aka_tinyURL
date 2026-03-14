from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

from src.redirect import router as redirect_router


def test_redirect_cached_hit(client, monkeypatch):
    monkeypatch.setattr(
        redirect_router,
        "get_cache",
        AsyncMock(
            return_value={
                "id": str(UUID("44444444-4444-4444-4444-444444444444")),
                "original_url": "https://example.com/cached",
                "expires_at": None,
            }
        ),
    )
    monkeypatch.setattr(redirect_router, "increment_click_count", AsyncMock())

    response = client.get("/cached", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/cached"


def test_redirect_cached_expired(client, monkeypatch):
    monkeypatch.setattr(
        redirect_router,
        "get_cache",
        AsyncMock(
            return_value={
                "id": str(UUID("55555555-5555-5555-5555-555555555555")),
                "original_url": "https://example.com/expired",
                "expires_at": "2000-01-01T00:00:00",
            }
        ),
    )

    response = client.get("/expired", follow_redirects=False)

    assert response.status_code == 410


def test_redirect_not_found(client, monkeypatch):
    monkeypatch.setattr(redirect_router, "get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(redirect_router, "get_link_by_short_code", AsyncMock(return_value=None))

    response = client.get("/missing", follow_redirects=False)

    assert response.status_code == 404


def test_redirect_db_expired(client, monkeypatch):
    expired_link = SimpleNamespace(
        id=UUID("66666666-6666-6666-6666-666666666666"),
        original_url="https://example.com/old",
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    monkeypatch.setattr(redirect_router, "get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(redirect_router, "get_link_by_short_code", AsyncMock(return_value=expired_link))

    response = client.get("/old", follow_redirects=False)

    assert response.status_code == 410


def test_redirect_db_success(client, monkeypatch):
    active_link = SimpleNamespace(
        id=UUID("77777777-7777-7777-7777-777777777777"),
        original_url="https://example.com/active",
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    monkeypatch.setattr(redirect_router, "get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(redirect_router, "get_link_by_short_code", AsyncMock(return_value=active_link))
    monkeypatch.setattr(redirect_router, "set_cache", AsyncMock())
    monkeypatch.setattr(redirect_router, "increment_click_count", AsyncMock())

    response = client.get("/active", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/active"
