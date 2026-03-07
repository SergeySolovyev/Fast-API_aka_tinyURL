from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.config import REDIS_URL, APP_HOST, APP_PORT, CLEANUP_INTERVAL_HOURS, UNUSED_LINKS_DAYS
from src.auth.users import auth_backend, fastapi_users
from src.auth.schemas import UserCreate, UserRead
from src.cache import init_redis, close_redis
from src.database import async_session_maker
from src.links.service import delete_expired_links, delete_unused_links
from src.links.router import router as links_router
from src.redirect.router import router as redirect_router


async def periodic_cleanup():
    """Background task: clean up expired and unused links periodically"""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_HOURS * 3600)
        try:
            async with async_session_maker() as session:
                expired = await delete_expired_links(session)
                unused = await delete_unused_links(session, UNUSED_LINKS_DAYS)
                if expired or unused:
                    print(f"🧹 Cleanup: {expired} expired, {unused} unused links removed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize Redis cache and background tasks on startup"""
    await init_redis()
    print(f"✅ Redis connected: {REDIS_URL}")
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()
    await close_redis()


app = FastAPI(
    title="BTFL link API",
    description="A FastAPI service for shortening URLs — beautiful links, fast and trackable",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Main application routes
app.include_router(links_router)

# Static directory
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """Serve the web UI"""
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.get("/api", tags=["Root"])
async def api_info():
    """API info endpoint"""
    return {
        "message": "BTFL link API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Register dynamic short-code redirect routes last
app.include_router(redirect_router)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level="info"
    )
