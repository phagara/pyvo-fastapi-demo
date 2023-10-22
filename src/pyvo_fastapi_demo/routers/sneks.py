import asyncio
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.datastructures import URL
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, col, select

from pyvo_fastapi_demo.dependencies import DB_ENGINE, DBSession, check_api_key
from pyvo_fastapi_demo.models import OperationResult, Snek, SnekCreate, SnekRead


class SnekNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snek not found!",
        )


SnekRouter = APIRouter(
    on_startup=[
        lambda: SQLModel.metadata.create_all(DB_ENGINE),
    ],
)


@SnekRouter.get("/", tags=["public"])
async def list_sneks(db: DBSession) -> list[SnekRead]:
    query = select(Snek).order_by(Snek.id_)
    return [SnekRead.from_orm(x) for x in db.exec(query).all()]


@SnekRouter.get("/snek/{snek_id}", tags=["public"])
async def get_snek(db: DBSession, snek_id: int) -> SnekRead:
    snek = db.get(Snek, snek_id)
    if snek is None:
        raise SnekNotFound()
    return SnekRead.from_orm(snek)


@SnekRouter.post(
    "/snek/{snek_id}/step",
    description="Don't try this at home!",
    deprecated=True,
    tags=["public"],
)
async def step_on_snek(db: DBSession, snek_id: int) -> OperationResult:
    snek = db.get(Snek, snek_id)
    if snek is None:
        raise SnekNotFound()
    return OperationResult(
        result="You died." if snek.venomous else "No step on Snek!",
    )


@SnekRouter.post(
    "/snek/{snek_id}/sleep",
    tags=["public"],
)
async def sleep_snek(db: DBSession, snek_id: int) -> OperationResult:
    snek = db.get(Snek, snek_id)
    if snek is None:
        raise SnekNotFound()
    await asyncio.sleep(3)
    growth_mm = secrets.randbelow(20) + 1
    snek.length += growth_mm / 1_000
    db.add(snek)
    db.commit()
    return OperationResult(
        result=f"{snek.species} had a nice nap and grew by {growth_mm} mm.",
    )


@SnekRouter.get(
    "/search",
    responses={
        status.HTTP_200_OK: {
            "headers": {
                "link": {
                    "description": "URL to the next page of results, if available.",
                },
            },
        },
    },
    tags=["public"],
)
async def search_sneks(
    request: Request,
    response: Response,
    db: DBSession,
    name: str | None = Query(default=None, description="Search by part of the Snek species name."),
    min_length: float | None = Query(default=0, description="Return Sneks at least this long (in meters)."),
    max_length: float | None = Query(default=None, description="Return Sneks at most this long (in meters)."),
    venomous: bool | None = Query(default=None, description="Return only (non-)venomous Sneks."),
    offset: int = Query(default=0, ge=0, description="Internal Snek ID to start the search from."),
    limit: int = Query(default=100, le=100, description="Return at most this many matching sneks."),
) -> list[SnekRead]:
    query = (
        select(Snek)
        .where(
            col(Snek.id_) >= offset,
            name is None or col(Snek.species).contains(name),
            min_length is None or col(Snek.length) >= min_length,
            max_length is None or col(Snek.length) <= max_length,
            venomous is None or col(Snek.venomous) == venomous,
        )
        .order_by(Snek.id_)
        .limit(limit)
    )
    sneks = [SnekRead.from_orm(x) for x in db.exec(query).all()]
    if sneks:
        links: dict[str, URL] = {}
        links["next"] = request.url.include_query_params(offset=sneks[-1].id_ + 1)
        response.headers["link"] = ", ".join([f'<{v}>; rel="{k}"' for k, v in links.items()])
    return sneks


@SnekRouter.post(
    "/snek",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "headers": {
                "location": {
                    "description": "URL of the new Snek",
                },
            },
        },
    },
    dependencies=[Depends(check_api_key)],
    tags=["admin"],
)
async def add_snek(
    request: Request,
    db: DBSession,
    snek: SnekCreate,
) -> RedirectResponse:
    db_snek = Snek.from_orm(snek)
    db.add(db_snek)
    db.commit()
    db.refresh(db_snek)
    return RedirectResponse(
        status_code=status.HTTP_201_CREATED,
        url=request.url_for("get_snek", snek_id=db_snek.id_),
    )


@SnekRouter.delete(
    "/snek/{snek_id}",
    dependencies=[Depends(check_api_key)],
    tags=["admin"],
)
async def remove_snek(db: DBSession, snek_id: int) -> SnekRead:
    snek = db.get(Snek, snek_id)
    if snek is None:
        raise SnekNotFound()
    db.delete(snek)
    db.commit()
    return SnekRead.from_orm(snek)
