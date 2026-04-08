"""FastAPI application entry point."""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database import init_db
from routes import auth, preferences, ideas, reviews, catalog

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="DateGen API",
    description="AI-powered date idea generator",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(preferences.router)
app.include_router(ideas.router)
app.include_router(reviews.router)
app.include_router(catalog.router)

FRONTEND_DIR = Path(__file__).resolve().parent / "static"
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    """Serve frontend app when available, else API metadata."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return {
        "message": "DateGen API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    """Serve SPA routes and static files for one-service deployment."""
    reserved_paths = {"docs", "redoc", "openapi.json", "health"}
    if full_path in reserved_paths or full_path.startswith(("api/", "auth/")):
        raise HTTPException(status_code=404, detail="Not Found")

    requested_file = FRONTEND_DIR / full_path
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)

    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "development") == "development",
    )
