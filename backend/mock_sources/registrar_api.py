
from fastapi import FastAPI, Query


app = FastAPI(
    title="DNSC Mock Registrar API",
    version="1.0.0"
)


STUDENTS = [
    {
        "id": "2023-0104",
        "name": "Ana Reyes",
        "program": "BSIT",
        "year": 4,
        "email": "ana@dnsc.edu.ph"
    },
    {
        "id": "2023-0105",
        "name": "Ben Cruz",
        "program": "BSIT",
        "year": "3",
        "email": "ben@dnsc.edu.ph"
    },
    {
        "id": "2023-0106",
        "name": "Carla Lim",
        "program": "BSIS",
        "year": 4,
        "email": "carla@dnsc.edu.ph"
    },
    {
        "id": "2023-0107",
        "name": "Invalid Demo Student",
        "program": "BSIT",
        "year": "3rd",
        "email": "invalid@dnsc.edu.ph"
    }
]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/students")
def get_students(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100)
):
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": STUDENTS[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(STUDENTS)
    }
