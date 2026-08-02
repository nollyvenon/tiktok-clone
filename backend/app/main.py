"""
TikTok Clone API - FastAPI Backend
Main entry point for the application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.routes import auth, profiles, videos, uploads, editor, ai, recommendations, search, hashtags, notifications

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    logger.info("Starting TikTok Clone API...")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down TikTok Clone API...")
    await close_db()
    logger.info("Database closed")

# Create FastAPI app
app = FastAPI(
    title="TikTok Clone API",
    description="Complete social video platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "tiktok-clone-api",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "TikTok Clone API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(profiles.router, prefix="/api", tags=["Profiles"])
app.include_router(videos.router, prefix="/api", tags=["Videos"])
app.include_router(uploads.router, prefix="/api", tags=["Uploads & Drafts"])
app.include_router(editor.router, prefix="/api", tags=["Video Editor"])
app.include_router(ai.router, prefix="/api", tags=["AI Creator Studio"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(search.router, prefix="/api", tags=["Search & Discovery"])
app.include_router(hashtags.router, prefix="/api", tags=["Hashtags & Trends"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
# TODO: Add more routers as they are implemented
# app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])
# app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])
# app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
# app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
# app.include_router(search.router, prefix="/api/search", tags=["Search"])

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
