"""
Database Setup Script
Creates required tables and schema for webhook service.

Usage:
    python setup_database.py
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import settings
from models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """
    Create all required database tables and schema.
    """
    logger.info("="*60)
    logger.info("🔧 Setting up Property-Office-DSS Webhook Database")
    logger.info("="*60 + "\n")

    # Create engine
    try:
        logger.info(f"Connecting to database: {settings.DATABASE_URL.split('@')[1]}")
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        logger.info("✓ Database connection successful\n")
    except SQLAlchemyError as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        return False

    # Create schema if it doesn't exist
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.DB_SCHEMA}"))
            conn.commit()
        logger.info(f"✓ Schema '{settings.DB_SCHEMA}' ready\n")
    except SQLAlchemyError as e:
        logger.error(f"✗ Failed to create schema: {e}")
        return False

    # Create tables
    try:
        logger.info("Creating tables from models...")
        Base.metadata.create_all(engine)
        logger.info("✓ All tables created successfully\n")
    except SQLAlchemyError as e:
        logger.error(f"✗ Failed to create tables: {e}")
        return False

    # Create additional indexes
    try:
        with engine.connect() as conn:
            indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_instrument_id ON {settings.DB_SCHEMA}.instrument(id)",
                f"CREATE INDEX IF NOT EXISTS idx_instrument_barcode ON {settings.DB_SCHEMA}.instrument(instrument_barcode)",
                f"CREATE INDEX IF NOT EXISTS idx_instrument_last_rented ON {settings.DB_SCHEMA}.instrument(instrument_last_rented)",
                f"CREATE INDEX IF NOT EXISTS idx_instrument_last_returned ON {settings.DB_SCHEMA}.instrument(instrument_last_returned)",
                f"CREATE INDEX IF NOT EXISTS idx_webhook_audit_instrument ON {settings.DB_SCHEMA}.webhook_audit_log(instrument_id)",
                f"CREATE INDEX IF NOT EXISTS idx_webhook_audit_created ON {settings.DB_SCHEMA}.webhook_audit_log(created_at)",
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                except SQLAlchemyError:
                    pass  # Index already exists
            
            conn.commit()
        logger.info("✓ Indexes created/verified\n")
    except SQLAlchemyError as e:
        logger.warning(f"⚠️  Could not create indexes: {e}\n")

    logger.info("="*60)
    logger.info("✓ Database setup completed successfully!")
    logger.info("="*60 + "\n")
    
    print("\nNext steps:")
    print("  1. Configure .env file with CHEQROOM_WEBHOOK_SECRET")
    print("  2. Set up webhook in Cheqroom dashboard")
    print("  3. Start the service: python main.py")
    print()
    
    return True


if __name__ == "__main__":
    success = setup_database()
    exit(0 if success else 1)
