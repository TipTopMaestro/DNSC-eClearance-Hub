from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import APP_NAME
from app.database import (
    init_db,
    init_additional_tables
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_additional_tables()

    print("Database initialized successfully.")

    yield


app = FastAPI(
    title=APP_NAME,
    description="DNSC e-Clearance Integration API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
def root():
    return {
        "message": "Welcome to DNSC e-Clearance Hub"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
