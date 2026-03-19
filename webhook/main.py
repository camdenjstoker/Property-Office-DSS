"""
Cheqroom Webhook Service - Entry Point
Starts the FastAPI server for webhook processing.

Usage:
    python main.py
    
Or with Uvicorn directly:
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import os
from dotenv import load_dotenv
import uvicorn
from config import settings

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def main():
    """Start the webhook service."""
    logger.info("="*60)
    logger.info("🚀 Starting Cheqroom Webhook Service")
    logger.info("="*60)
    
    # Log configuration (with sensitive values masked)
    config_dict = settings.to_dict()
    for key, value in config_dict.items():
        logger.info(f"   {key:20} = {value}")
    
    logger.info("="*60 + "\n")
    
    # Start server
    uvicorn.run(
        "app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
