import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import APP_NAME

from app.database import (
    init_db,
    init_additional_tables,
    init_registrar_tables
)

from app.routers import( auth, students, admin, deadlines, staff)


logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware
from app.config import FRONTEND_ORIGINS

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_additional_tables()
    init_registrar_tables()

    print("Database initialized successfully.")

    yield


app = FastAPI(
    title=APP_NAME,
    description="DNSC e-Clearance Integration API",
    version="1.0.0",
    lifespan=lifespan,
    debug=False
)

#CORS MIDDLEWARE 
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type"
    ]
)



# Register routers.
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(admin.router)
app.include_router(deadlines.router)
app.include_router(staff.router)

@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request data.",
            "errors": [
                {
                    "field": list(error["loc"]),
                    "type": error["type"]
                }
                for error in exc.errors()
            ]
        }
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception
):
    logger.error(
        "Unexpected server error: %s",
        type(exc).__name__
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred."
        }
    )


@app.get("/")
def root():
    return {
        "message": "Welcome to DNSC e-Clearance Hub"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
