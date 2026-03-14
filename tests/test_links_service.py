from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.links import service


class FakeScalarResult:
    def __init__(self, one=None, many=None):
        self._one = one
        self._many = many or []

    def scalar_one_or_none(self):
        return self._one

    def scalars(self):
        return self

    def all(self):
        return self._many


@pytest.mark.asyncio
async def test_generate_short_code_default_length():
    code = service.generate_short_code()

    assert len(code) == service.SHORT_CODE_LENGTH
    assert code.isalnum()


@pytest.mark.asyncio
async def test_build_short_url(monkeypatch):
    monkeypatch.setattr(service, "BASE_URL", "https://short.local")

    assert service.build_short_url("abc") == "https://short.local/abc"


@pytest.mark.asyncio
async def test_create_short_link_duplicate_alias_raises():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(one=object()))

    with pytest.raises(ValueError, match="already exists"):
        await service.create_short_link(
            session=session,
            original_url="https://example.com",
            custom_alias="taken",
        )


@pytest.mark.asyncio
async def test_create_short_link_custom_alias_success(monkeypatch):
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(one=None))

    async def fake_refresh(link):
        return None

    session.refresh = fake_refresh

    link = await service.create_short_link(
        session=session,
        original_url="https://example.com",
        custom_alias="myalias",
    )

    assert link.short_code == "myalias"
    assert link.original_url == "https://example.com"


@pytest.mark.asyncio
async def test_get_link_by_short_code_returns_link():
    expected = object()
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(one=expected))

    result = await service.get_link_by_short_code(session, "abc")

    assert result is expected


@pytest.mark.asyncio
async def test_increment_click_count_calls_commit():
    session = AsyncMock()

    await service.increment_click_count(session, UUID("88888888-8888-8888-8888-888888888888"))

    assert session.execute.await_count == 1
    assert session.commit.await_count == 1


@pytest.mark.asyncio
async def test_search_link_by_url_returns_all():
    links = [object(), object()]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(many=links))

    result = await service.search_link_by_url(session, "https://example.com")

    assert result == links


@pytest.mark.asyncio
async def test_delete_expired_links_deletes_each():
    links = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(many=links))

    count = await service.delete_expired_links(session)

    assert count == 2
    assert session.delete.await_count == 2
    assert session.commit.await_count == 1


@pytest.mark.asyncio
async def test_delete_unused_links_deletes_each():
    links = [SimpleNamespace(id=1)]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(many=links))

    count = await service.delete_unused_links(session, days=30)

    assert count == 1
    assert session.delete.await_count == 1
    assert session.commit.await_count == 1


@pytest.mark.asyncio
async def test_create_short_link_auto_generates_code():
    """Covers the while-loop: first code collides, second is free."""
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            FakeScalarResult(one=object()),  # first random code already taken
            FakeScalarResult(one=None),      # second code is free
        ]
    )

    async def fake_refresh(link):
        return None

    session.refresh = fake_refresh

    link = await service.create_short_link(
        session=session,
        original_url="https://example.com/auto",
    )

    assert link.short_code is not None
    assert len(link.short_code) == service.SHORT_CODE_LENGTH


@pytest.mark.asyncio
async def test_create_short_link_zero_expiration(monkeypatch):
    """When DEFAULT_LINK_EXPIRATION_DAYS=0, expires_at stays None."""
    monkeypatch.setattr(service, "DEFAULT_LINK_EXPIRATION_DAYS", 0)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeScalarResult(one=None))

    async def fake_refresh(link):
        return None

    session.refresh = fake_refresh

    link = await service.create_short_link(
        session=session,
        original_url="https://example.com/noexpiry",
    )

    assert link.expires_at is None
