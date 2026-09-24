from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_api_contract(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.router.on_startup.clear()
    client = TestClient(app)
    response = client.get("/api/metrics/overview")
    assert response.status_code == 200
    assert response.json()["total_requests"] == 0
    response = client.get("/api/requests?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["items"] == []
    app.dependency_overrides.clear()
