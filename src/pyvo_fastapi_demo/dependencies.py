from typing import Annotated, Iterator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlmodel import Session, create_engine

DB_ENGINE = create_engine(
    "sqlite:///pyvo-fastapi-demo.sqlite3",
    echo=True,
    connect_args={"check_same_thread": False},
)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
SECRET_API_KEY = "sikrit"


def db_session() -> Iterator[Session]:
    with Session(DB_ENGINE) as session:
        yield session


def check_api_key(
    key: Annotated[str, Security(API_KEY_HEADER)],
) -> None:
    if key != SECRET_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key!",
        )


DBSession = Annotated[Session, Depends(db_session)]
