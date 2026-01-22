from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.cache.router import cache_route
from app.auth.router import auth_router
from app.database.main import init_db

@asynccontextmanager
async def life_span(app: FastAPI):
    print("starting server")
    await init_db()
    yield
    print("Stopping server")

version = "v1"

def register_routers(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(cache_route)


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=life_span,
        title="Cache project",
        description="A REST API for storing files and retrieving it fast using cache ",
        version=version,
        docs_url=f"/api/{version}/docs",
        redoc_url=f"/api/{version}/redoc",
        contact={
            "name": "random",
            "email": "oreelijah33@gmail.com"
        }
    )

    register_routers(app)
    return app