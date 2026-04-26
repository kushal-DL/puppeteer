from fastapi import FastAPI

from routes.generation import router as generation_router
from routes.status import router as status_router
from routes.webhook import router as webhook_router

app = FastAPI()
app.include_router(status_router)
app.include_router(generation_router)
app.include_router(webhook_router)
