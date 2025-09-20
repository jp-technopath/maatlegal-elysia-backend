from fastapi import FastAPI

from .config_shared import router as config_shared_router

app = FastAPI()

app.include_router(config_shared_router)
