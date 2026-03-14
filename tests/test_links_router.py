from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

from src.links import router as links_router


def make_link(short_code="abc123", user_id=None):
    return SimpleNamespace(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        short_code=short_code,
        original_url="https://example.com/page",
        custom_alias=None,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=10),
        click_count=0,
        last_used_at=None,
        category=None,
        user_id=user_id,
    )


def test_shorten_url_success(client, monkeypatch):
    link = make_link()
    monkeypatch.setattr(links_router, "create_short_link", AsyncMock(return_value=link))
    monkeypatch.setattr(links_router, "delete_cache", AsyncMock())

    response = client.post("/links/shorten", json={"original_url": "https://example.com"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["short_code"] == "abc123"
    assert payload["original_url"] == "https://example.com/page"


def test_shorten_url_bad_alias(client, monkeypatch):
    monkeypatch.setattr(links_router, "create_short_link", AsyncMock(side_effect=ValueError("Alias exists")))

    response = client.post(
        "/links/shorten",
        json={"original_url": "https://example.com", "custom_alias": "alias"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Alias exists"


def test_get_link_stats_cache_hit(client, monkeypatch):
    now = datetime.utcnow().isoformat()
    monkeypatch.setattr(
        links_router,
        "get_cache",
        AsyncMock(
            return_value={
                "short_code": "abc123",
                "original_url": "https://example.com/page",
                "created_at": now,
                "expires_at": None,
                "click_count": 7,
                "last_used_at": None,
                "category": None,
            }
        ),
    )

    response = client.get("/links/abc123/stats")

    assert response.status_code == 200
    assert response.json()["click_count"] == 7


def test_get_link_stats_not_found(client, monkeypatch):
    monkeypatch.setattr(links_router, "get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=None))

    response = client.get("/links/missing/stats")

    assert response.status_code == 404
    assert response.json()["detail"] == "Short link not found"


def test_delete_link_forbidden(client, monkeypatch):
    another_user = UUID("33333333-3333-3333-3333-333333333333")
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=make_link(user_id=another_user)))

    response = client.delete("/links/abc123")

    assert response.status_code == 403


def test_delete_link_success(client, monkeypatch):
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=make_link(user_id=owner_id)))
    monkeypatch.setattr(links_router, "delete_cache", AsyncMock())

    response = client.delete("/links/abc123")

    assert response.status_code == 204


def test_update_link_success(client, monkeypatch):
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    link = make_link(user_id=owner_id)
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=link))
    monkeypatch.setattr(links_router, "delete_cache", AsyncMock())

    response = client.put(
        "/links/abc123",
        json={
            "original_url": "https://new.example.com",
            "category": "news",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["short_code"] == "abc123"
    assert payload["original_url"] == "https://new.example.com/"


def test_search_links(client, monkeypatch):
    monkeypatch.setattr(links_router, "search_link_by_url", AsyncMock(return_value=[make_link("s1")]))

    response = client.get("/links/search/by-url", params={"original_url": "https://example.com/page"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["short_code"] == "s1"


def test_cleanup_endpoints(client, monkeypatch):
    monkeypatch.setattr(links_router, "delete_expired_links", AsyncMock(return_value=2))
    monkeypatch.setattr(links_router, "delete_unused_links", AsyncMock(return_value=3))

    expired = client.delete("/links/cleanup/expired")
    unused = client.delete("/links/cleanup/unused", params={"days": 45})

    assert expired.status_code == 200
    assert expired.json()["deleted"] == 2
    assert unused.status_code == 200
    assert unused.json()["deleted"] == 3


def test_get_link_stats_db_found(client, monkeypatch):
    """Cache miss but link found in DB — covers set_cache path."""
    link = make_link()
    monkeypatch.setattr(links_router, "get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=link))
    monkeypatch.setattr(links_router, "set_cache", AsyncMock())

    response = client.get("/links/abc123/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "abc123"
    assert data["click_count"] == 0


def test_delete_link_not_found(client, monkeypatch):
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=None))

    response = client.delete("/links/nonexistent")

    assert response.status_code == 404


def test_update_link_not_found(client, monkeypatch):
    monkeypatch.setattr(links_router, "get_link_by_short_code", AsyncMock(return_value=None))

    response = client.put("/links/nonexistent", json={"original_url": "https://new.example.com"})

    assert response.status_code == 404


def test_update_link_forbidden(client, monkeypatch):
    another_user = UUID("33333333-3333-3333-3333-333333333333")
    monkeypatch.setattr(
        links_router, "get_link_by_short_code", AsyncMock(return_value=make_link(user_id=another_user))
    )

    response = client.put("/links/abc123", json={"original_url": "https://new.example.com"})

    assert response.status_code == 403


def test_get_my_links_empty(client):
    """Returns empty list when user has no links (DummySession returns [])."""
    response = client.get("/links/user/my-links")

    assert response.status_code == 200
    assert response.json() == []
