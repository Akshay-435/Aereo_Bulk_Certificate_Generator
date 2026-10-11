import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings
from app.database import Base, get_db


@pytest.fixture(scope="session")
def test_dir():
    """Creates a temporary root directory for test databases and PDF output."""
    temp_path = tempfile.mkdtemp(prefix="test_cert_gen_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="session")
def test_engine(test_dir):
    """Creates a temporary SQLite database engine for testing."""
    db_file = os.path.join(test_dir, "test.db")
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def TestSessionLocal(test_engine):
    """Factory for test DB sessions."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_environment(test_dir, test_engine, monkeypatch):
    """Configures environment settings for isolated test execution."""
    output_dir = os.path.join(test_dir, "generated_certificates")
    os.makedirs(output_dir, exist_ok=True)

    monkeypatch.setattr(settings, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(settings, "MAX_BATCH_SIZE", 10)  # Lower batch size for easier testing

    # Clean tables before each test
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield output_dir


@pytest.fixture
def db_session(TestSessionLocal):
    """Provides a fresh database session for unit tests."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(TestSessionLocal):
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
