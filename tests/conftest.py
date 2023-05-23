"""Config for PyTest."""

import pytest
from tortoise import Tortoise
from tortoise.contrib.test import finalizer, initializer


@pytest.fixture(scope="session")
async def test_db():
    """Handle connection to test database."""
    await Tortoise.init(
        db_url="postgres://username:password@localhost:5432/testing",
        modules={"models": ["app.models.doi"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
    await Tortoise._drop_databases()


@pytest.fixture(autouse=True)
async def setup_test_db(test_db):
    """Setup test database."""
    initializer(["app.models.doi"])
    yield
    finalizer()
