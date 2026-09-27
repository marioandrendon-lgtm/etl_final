from fastapi import FastAPI
from .routes.cargas import router as cargas_router
from .routes.consultas import router as consultas_router

app = FastAPI(
    title="API ETL MIO",
    version="2.0.0",
)

app.include_router(
    cargas_router,
    prefix="/api/v1/cargas",
    tags=["cargas"],
)

app.include_router(
    consultas_router,
    prefix="/api/v1/consultas",
    tags=["consultas"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
