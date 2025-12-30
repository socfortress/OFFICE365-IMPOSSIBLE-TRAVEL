import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger
from routes.analyze import analyze_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Office 365 Impossible Travel Detection API",
    description="Detects impossible travel patterns based on user login locations and timestamps",
    version="1.0.0",
)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger.add(
    "impossible_travel.log",
    format="{time} {level} {message}",
    level=log_level,
    rotation="10 MB",
    compression="zip",
)

# Include routers
app.include_router(analyze_router)

logger.info("Office 365 Impossible Travel Detection API initialized")
logger.info("Configuration loaded:")
logger.info(
    f"- Time Window: {os.getenv('IMPOSSIBLE_TRAVEL_TIME_WINDOW', '5')} minutes",
)
logger.info(f"- Max Records Per User: {os.getenv('MAX_RECORDS_PER_USER', '10')}")
logger.info(
    f"- Database Path: {os.getenv('DATABASE_PATH', './data/impossible_travel.db')}",
)


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Office 365 Impossible Travel Detection API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze?query=user=email|ip=1.2.3.4|ts=2025-12-10T10:17:54",
            "purge": "/purge (POST)",
            "stats": "/stats",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "impossible-travel-detection"}


if __name__ == "__main__":
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "80"))
    logger.info(f"Starting API server on {api_host}:{api_port}")
    uvicorn.run(app, host=api_host, port=api_port)
