"""Configuration pytest pour AI Orchestrator v8.2.0"""

import os
import sys
from pathlib import Path

# CRITICAL: Set TESTING=1 BEFORE any import to disable slowapi
os.environ["TESTING"] = "1"
# Use test PostgreSQL database
os.environ["DATABASE_URL"] = (
    "postgresql://lalpha:lalpha2024secure@127.0.0.1:5432/ai_orchestrator_test"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def workspace_dir():
    """Retourne le chemin du workspace"""
    from app.core.config import settings

    return settings.WORKSPACE_DIR


@pytest.fixture
def test_file(workspace_dir, tmp_path):
    """Cree un fichier de test temporaire dans le workspace"""
    from pathlib import Path

    test_path = Path(workspace_dir) / "pytest_temp.txt"
    test_path.write_text("test content")
    yield test_path
    if test_path.exists():
        test_path.unlink()


# Fixtures pour tests API
@pytest.fixture(scope="function")
def db_session():
    """Create test DB session using PostgreSQL test database"""
    from app.core.database import Base

    TEST_DATABASE_URL = "postgresql://lalpha:lalpha2024secure@127.0.0.1:5432/ai_orchestrator_test"
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Client API test"""
    from app.core.database import get_db
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable rate limiting for tests (slowapi incompatible with TestClient)
    original_limit = None
    if hasattr(app.state, "limiter"):
        original_limit = app.state.limiter.limit

        def no_op_limit(limit_value):
            """Decorator that does nothing during tests"""

            def decorator(func):
                return func

            return decorator

        app.state.limiter.limit = no_op_limit

    yield TestClient(app)

    # Restore after tests
    if hasattr(app.state, "limiter") and original_limit is not None:
        app.state.limiter.limit = original_limit

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient):
    """Token JWT pour tests authentifies"""
    # Create test user
    response = client.post(
        "/api/v1/auth/register", json={"username": "testuser", "password": "testpass123"}
    )

    # Login
    response = client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "testpass123"}
    )

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
