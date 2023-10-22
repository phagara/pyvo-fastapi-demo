from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from pyvo_fastapi_demo.routers.sneks import SnekRouter

app = FastAPI()
app.include_router(
    SnekRouter,
    prefix="/sneks",
)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse("/docs")
