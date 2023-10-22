import time

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from pyvo_fastapi_demo.dependencies import SECRET_API_KEY
from pyvo_fastapi_demo.dependencies import db_session as orig_db_session
from pyvo_fastapi_demo.main import app
from pyvo_fastapi_demo.models import Snek


@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def get_db_session_override():
        yield db_session

    app.dependency_overrides[orig_db_session] = get_db_session_override
    yield TestClient(app)
    del app.dependency_overrides[orig_db_session]


def test_root_redirect(client: TestClient):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_create_snek(client: TestClient):
    response = client.post(
        "/sneks/snek",
        json={
            "species": "Indian Python",
            "length": 3,
            "venomous": False,
        },
        headers={
            "X-API-Key": SECRET_API_KEY,
        },
    )
    assert response.status_code == 201
    assert "location" in response.headers
    assert response.headers["location"].endswith("/snek/1")


def test_create_snek_unauth(client: TestClient):
    response = client.post(
        "/sneks/snek",
        json={
            "species": "Indian Python",
            "length": 3,
            "venomous": False,
        },
    )
    assert response.status_code == 403


def test_create_snek_badauth(client: TestClient):
    response = client.post(
        "/sneks/snek",
        json={
            "species": "Indian Python",
            "length": 3,
            "venomous": False,
        },
        headers={
            "X-API-Key": "incorrect",
        },
    )
    assert response.status_code == 401


def test_create_snek_incomplete(client: TestClient):
    response = client.post(
        "/sneks/snek",
        json={
            "species": "Incomplete Python",
        },
        headers={
            "X-API-Key": SECRET_API_KEY,
        },
    )
    assert response.status_code == 422


def test_create_snek_invalid(client: TestClient):
    response = client.post(
        "/sneks/snek",
        json={
            "species": "Impossible Python",
            "length": 420.69,
            "venomous": "maybe?",
        },
        headers={
            "X-API-Key": SECRET_API_KEY,
        },
    )
    assert response.status_code == 422


def test_list_sneks(db_session: Session, client: TestClient):
    sneks = [
        Snek(species="Indian Python", length=3, venomous=False),
        Snek(species="King Cobra", length=3.6, venomous=True),
    ]
    for snek in sneks:
        db_session.add(snek)
    db_session.commit()
    for snek in sneks:
        db_session.refresh(snek)

    response = client.get("/sneks")
    data = response.json()

    assert response.status_code == 200

    assert len(data) == len(sneks)
    for idx, item in enumerate(data):
        assert item["id"] == sneks[idx].id_
        assert item["species"] == sneks[idx].species
        assert item["length"] == sneks[idx].length
        assert item["venomous"] == sneks[idx].venomous


def test_list_sneks_empty(client: TestClient):
    response = client.get("/sneks")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 0


def test_get_snek(db_session: Session, client: TestClient):
    snek = Snek(species="Grass Snake", length=1, venomous=False)
    db_session.add(snek)
    db_session.commit()
    db_session.refresh(snek)

    response = client.get(f"/sneks/snek/{snek.id_}")
    data = response.json()

    assert response.status_code == 200
    assert data["species"] == snek.species
    assert data["length"] == snek.length
    assert data["venomous"] == snek.venomous
    assert data["id"] == snek.id_


def test_get_snek_nonexistent(client: TestClient):
    response = client.get("/sneks/snek/42")
    assert response.status_code == 404


def test_step_on_snek(db_session: Session, client: TestClient):
    sneks = [
        Snek(species="Indian Python", length=3, venomous=False),
        Snek(species="King Cobra", length=3.6, venomous=True),
    ]
    for snek in sneks:
        db_session.add(snek)
    db_session.commit()
    for snek in sneks:
        db_session.refresh(snek)
        response = client.post(f"/sneks/snek/{snek.id_}/step")
        data = response.json()
        assert response.status_code == 200
        if snek.venomous:
            assert data["result"] == "You died."
        else:
            assert data["result"] == "No step on Snek!"


def test_step_on_snek_nonexistent(client: TestClient):
    response = client.post("/sneks/snek/42/step")
    assert response.status_code == 404


def test_sleep_snek(db_session: Session, client: TestClient):
    snek = Snek(species="Indian Python", length=3, venomous=False)
    db_session.add(snek)
    db_session.commit()
    start = time.monotonic()
    response = client.post(f"/sneks/snek/{snek.id_}/sleep")
    assert time.monotonic() - start >= 3
    assert response.status_code == 200
    db_session.refresh(snek)
    assert snek.length > 3


def test_sleep_snek_nonexistent(client: TestClient):
    response = client.post("/sneks/snek/42/sleep")
    assert response.status_code == 404


def test_delete_snek(db_session: Session, client: TestClient):
    snek = Snek(species="Boa Constrictor", length=2.3, venomous=False)
    db_session.add(snek)
    db_session.commit()
    db_session.refresh(snek)

    response = client.delete(
        f"/sneks/snek/{snek.id_}",
        headers={
            "X-API-Key": SECRET_API_KEY,
        },
    )
    assert response.status_code == 200

    db_snek = db_session.get(Snek, snek.id_)
    assert db_snek is None


def test_delete_snek_unauth(client: TestClient):
    response = client.delete(
        "/sneks/snek/42",
    )
    assert response.status_code == 403


def test_delete_snek_nonexistent(client: TestClient):
    response = client.delete(
        "/sneks/snek/42",
        headers={
            "X-API-Key": SECRET_API_KEY,
        },
    )
    assert response.status_code == 404


def test_search_sneks(db_session: Session, client: TestClient):
    sneks = [
        Snek(species="Indian Python", length=3, venomous=False),
        Snek(species="Baby Indian Python", length=0.5, venomous=False),
        Snek(species="Godzilla Indian Python", length=10, venomous=False),
        Snek(species="King Cobra", length=3.6, venomous=True),
    ]
    for snek in sneks:
        db_session.add(snek)
    db_session.commit()

    response = client.get("/sneks/search?name=Python")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 3
    assert "link" in response.headers
    assert 'rel="next"' in response.headers["link"]

    response = client.get("/sneks/search?min_length=5")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert "link" in response.headers
    assert 'rel="next"' in response.headers["link"]

    response = client.get("/sneks/search?max_length=3")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert "link" in response.headers
    assert 'rel="next"' in response.headers["link"]

    response = client.get("/sneks/search?venomous=true")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert "link" in response.headers
    assert 'rel="next"' in response.headers["link"]

    response = client.get("/sneks/search?min_length=5&venomous=true")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 0
    assert "link" not in response.headers

    response = client.get("/sneks/search?limit=2")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert "link" in response.headers
    assert 'rel="next"' in response.headers["link"]
