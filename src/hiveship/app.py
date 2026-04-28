from fastapi import FastAPI

from hiveship.logging import setup_logging
from hiveship.routes.generation import router as generation_router
from hiveship.routes.status import router as status_router
from hiveship.routes.webhook import router as webhook_router

setup_logging()

app = FastAPI(title="HiveShip", version="0.1.0")
app.include_router(status_router)
app.include_router(generation_router)
app.include_router(webhook_router)
