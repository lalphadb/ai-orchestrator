"""Configuration pytest pour AI Orchestrator v6.1"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter le backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def workspace_dir():
    """Retourne le chemin du workspace"""
    from app.core.config import settings

    return settings.WORKSPACE_DIR


@pytest.fixture
def test_file(workspace_dir, tmp_path):
    """Crée un fichier de test temporaire dans le workspace"""
    from pathlib import Path

    test_path = Path(workspace_dir) / "pytest_temp.txt"
    test_path.write_text("test content")
    yield test_path
    if test_path.exists():
        test_path.unlink()


# Fixtures pour tests API
@pytest.fixture(scope="function")
def db_session():
    """Créer session DB test en mémoire"""
    from app.core.database import Base, get_db

    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient):
    """Token JWT pour tests authentifiés"""
    # Créer user test
    response = client.post(
        "/api/v1/auth/register", json={"username": "testuser", "password": "testpass123"}
    )

    # Login
    response = client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "testpass123"}
    )

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
