from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session
from sqlalchemy import text
from database import engine
from routes import tasks, chat
from config import settings
from agent import startup_agent, shutdown_agent
from schemas import ErrorResponse
from models import Conversation, Message, Task  # Import models to register them with SQLModel
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to initialize the database
    """
    logger.info("Initializing database...")
    # Create tables if they don't exist (keeps existing data)
    SQLModel.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")
    # Start the AI agent and MCP server
    try:
        await startup_agent()
        logger.info("AI agent initialized successfully")
    except Exception as e:
        logger.warning(f"AI agent failed to start: {e}. Chat endpoint will be unavailable.")
    yield
    # Shutdown the AI agent and MCP server
    await shutdown_agent()
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Todo Backend API",
    description="Secure, scalable backend API for the Todo application with JWT-based authentication and user isolation",
    version="2.0.0",
    lifespan=lifespan
)


# Parse additional CORS origins from settings
additional_origins = []
if settings.cors_origins:
    additional_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routes
app.include_router(tasks.router)
app.include_router(chat.router)


@app.get("/")
def read_root():
    """
    Root endpoint
    """
    return {"message": "Todo Chatbot API is running", "version": "2.0.0"}


@app.get("/health")
def health_check():
    """
    Health check endpoint that verifies database connectivity
    """
    try:
        from database import get_session
        from sqlmodel import Session

        # Attempt to create a session and execute SELECT 1 to verify DB connectivity
        with Session(engine) as session:
            result = session.exec(text("SELECT 1")).first()
            if result is not None:
                return {"status": "healthy", "service": "todo-chatbot-api", "database": "connected"}
            else:
                return {"status": "degraded", "service": "todo-chatbot-api", "database": "disconnected"}
    except Exception:
        return {"status": "degraded", "service": "todo-chatbot-api", "database": "disconnected"}


from fastapi.responses import JSONResponse


from sqlalchemy.exc import OperationalError


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global handler for HTTP exceptions
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "message": exc.detail
        }
    )


@app.exception_handler(OperationalError)
async def database_error_handler(request, exc):
    """
    Global handler for database operational errors
    """
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database temporarily unavailable"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )