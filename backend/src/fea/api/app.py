"""
Main FastAPI Application Entry Point for Nonlinear FEA Studio.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fea.api.routes import router as api_router

app = FastAPI(
    title="Nonlinear FEA Studio API",
    description="Nonlinear, Multiscale Computational Structural Mechanics Framework Backend",
    version="0.1.0"
)

# Enable CORS for Vite frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "Nonlinear FEA Studio",
        "version": "0.1.0",
        "docs_url": "/docs",
        "status": "online"
    }
