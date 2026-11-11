import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import relatos, visao

app = FastAPI(title="CitizenTech API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(relatos.router)
app.include_router(visao.router)


@app.get("/health")
def health():
    return {"status": "ok"}
