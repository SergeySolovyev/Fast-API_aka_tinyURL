from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.auth.users import current_active_user, current_user_optional
from src.database import get_async_session
from src.main import app


TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


class DummyResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return self

    def all(self):
        return self._data


class DummySession:
    async def execute(self, *_args, **_kwargs):
        return DummyResult([])

    async def delete(self, *_args, **_kwargs):
        return None

    async def commit(self):
        return None

    async def refresh(self, _obj):
        return None


@pytest.fixture
def test_user():
    return SimpleNamespace(id=TEST_USER_ID)


@pytest.fixture
def client(test_user):
    async def override_get_async_session():
        yield DummySession()

    async def override_current_active_user():
        return test_user

    async def override_current_user_optional():
        return None

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[current_active_user] = override_current_active_user
    app.dependency_overrides[current_user_optional] = override_current_user_optional

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
