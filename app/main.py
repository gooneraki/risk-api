""" Main application entry point for the risk metrics API. """
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes.risk_routes import router as risk_router
from app.routes.user_routes import router as user_router
from app.routes.portfolio_routes import router as portfolio_router
from app.db import init_db
from app.redis_service import redis_service


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """ Initialize the database and Redis connection. """
    # Initialize database
    init_db()

    # Initialize Redis connection
    try:
        await redis_service.connect()
        print("🚀 Risk API started with Redis Pub/Sub support")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("📝 Continuing without Redis (some features may be limited)")

    yield

    # Cleanup
    try:
        await redis_service.disconnect()
        print("🔌 Redis connection closed")
    except Exception as e:
        print(f"⚠️  Error closing Redis connection: {e}")

    print("Shutting down...")

app = FastAPI(
    lifespan=lifespan,
    title="Risk API",
    description="A comprehensive risk management API",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """ Root endpoint. """
    return {"message": "Welcome to the Risk API"}


@app.get("/favicon.ico")
def favicon():
    """ Favicon endpoint to serve the favicon.ico file. """
    return FileResponse(
        "app/static/favicon.ico",
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@app.get("/healthz")
def healthz():
    """ Health check endpoint. """
    return {"status": "ok"}


app.include_router(risk_router)
app.include_router(user_router)
app.include_router(portfolio_router)
