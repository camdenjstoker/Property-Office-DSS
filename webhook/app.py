from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

# ==========================================
# LOGGING SETUP
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
app = FastAPI()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://propoff:student@localhost:5432/propertyoffice"
)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cheqroom webhook secret (MUST be stored in environment variable)
WEBHOOK_SECRET = os.getenv("CHEQROOM_WEBHOOK_SECRET", "your_webhook_secret_here")

if WEBHOOK_SECRET == "your_webhook_secret_here":
    logger.warning("⚠️  WEBHOOK_SECRET not set! Using default value.")


# ==========================================
# PHASE 1: SIGNATURE VERIFICATION
# ==========================================

def verify_signature(body: bytes, signature_header: str) -> bool:
    """
    Verify the X-CHEQROOM-Signature HMAC header.
    
    Args:
        body: Raw request body (bytes)
        signature_header: X-CHEQROOM-Signature header value
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Calculate HMAC-SHA256 of the body
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare using constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_signature, signature_header)
        
        if not is_valid:
            logger.warning(
                f"Signature mismatch. Expected: {expected_signature[:16]}..., "
                f"Got: {signature_header[:16] if signature_header else 'None'}..."
            )
        
        return is_valid
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


# ==========================================
# PHASE 2: TIMESTAMP COMPARISON LOGIC
# ==========================================

def should_update_instrument(
    db: Session,
    instrument_id: int,
    incoming_timestamp: datetime
) -> bool:
    """
    Determine if the incoming update is newer than the current DB record.
    Implements "newer-wins" conflict resolution.
    
    Args:
        db: SQLAlchemy session
        instrument_id: The instrument to check
        incoming_timestamp: Timestamp from Cheqroom webhook
    
    Returns:
        True if update should proceed, False if it's older data
    """
    try:
        # Query current timestamp (lock the row for update)
        result = db.execute(
            text(
                """
                SELECT instrument_last_rented, instrument_last_returned
                FROM public.instrument
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": instrument_id}
        ).fetchone()
        
        if not result:
            logger.warning(f"Instrument {instrument_id} not found in database")
            return False
        
        current_rented, current_returned = result
        
        # Determine the most recent timestamp in the DB
        current_max_timestamp = None
        if current_rented:
            current_max_timestamp = current_rented
        if current_returned and (current_max_timestamp is None or current_returned > current_max_timestamp):
            current_max_timestamp = current_returned
        
        # Compare timestamps
        if current_max_timestamp is None:
            # No previous record, allow the update
            logger.info(f"Instrument {instrument_id}: No previous timestamp, allowing update")
            return True
        
        if incoming_timestamp > current_max_timestamp:
            logger.info(
                f"Instrument {instrument_id}: Incoming timestamp ({incoming_timestamp}) "
                f"is newer than DB ({current_max_timestamp}), allowing update"
            )
            return True
        else:
            logger.info(
                f"Instrument {instrument_id}: Incoming timestamp ({incoming_timestamp}) "
                f"is older than DB ({current_max_timestamp}), discarding update"
            )
            return False
    
    except Exception as e:
        logger.error(f"Error comparing timestamps for instrument {instrument_id}: {e}")
        return False


# ==========================================
# PHASE 3 & 4: CHECK-IN/CHECK-OUT LOGIC
# ==========================================

def process_webhook_update(
    db: Session,
    instrument_id: int,
    event_type: str,
    timestamp: datetime,
    user_info: Dict[str, Any],
    transaction_id: Optional[str] = None,
    condition: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process the webhook update with appropriate branching logic.
    
    Args:
        db: SQLAlchemy session
        instrument_id: Target instrument ID
        event_type: "checked_out" or "checked_in"
        timestamp: The updatedAt timestamp from Cheqroom
        user_info: User details (f_name, l_name)
        transaction_id: Optional transaction ID from Cheqroom
        condition: Optional condition update ("good", "fair", "poor", etc.)
    
    Returns:
        Dictionary with update status and details
    """
    try:
        # Phase 3: Branch based on event type
        if event_type == "checked_out":
            db.execute(
                text(
                    """
                    UPDATE public.instrument
                    SET instrument_last_rented = :timestamp
                    WHERE id = :id
                    """
                ),
                {"timestamp": timestamp, "id": instrument_id}
            )
            action = "checked_out"
        elif event_type == "checked_in":
            db.execute(
                text(
                    """
                    UPDATE public.instrument
                    SET instrument_last_returned = :timestamp
                    WHERE id = :id
                    """
                ),
                {"timestamp": timestamp, "id": instrument_id}
            )
            action = "checked_in"
        else:
            return {
                "status": "error",
                "reason": f"Unknown event type: {event_type}"
            }
        
        # Update condition if provided
        if condition:
            db.execute(
                text(
                    """
                    UPDATE public.instrument
                    SET instrument_condition = :condition
                    WHERE id = :id
                    """
                ),
                {"condition": condition, "id": instrument_id}
            )
        
        # Phase 4: Audit logging
        user_name = f"{user_info.get('f_name', 'Unknown')} {user_info.get('l_name', '')}"
        log_message = (
            f"Webhook Update | Action: {action} | Instrument: {instrument_id} | "
            f"User: {user_name} | Timestamp: {timestamp}"
        )
        if transaction_id:
            log_message += f" | Transaction ID: {transaction_id}"
        
        logger.info(log_message)
        
        return {
            "status": "updated",
            "action": action,
            "instrument_id": instrument_id,
            "user": user_name,
            "timestamp": timestamp.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return {
            "status": "error",
            "reason": str(e)
        }


# ==========================================
# MAIN WEBHOOK ENDPOINT
# ==========================================

@app.post("/webhooks/cheqroom")
async def cheqroom_webhook(request: Request):
    """
    Main webhook endpoint for Cheqroom check-in/check-out events.
    Implements all four phases of the webhook system.
    """
    # Capture raw body for signature verification
    body = await request.body()
    signature_header = request.headers.get("X-CHEQROOM-Signature")
    
    logger.info(f"Received webhook request. Signature header present: {signature_header is not None}")
    
    # ==========================================
    # PHASE 1: Signature Verification
    # ==========================================
    if not signature_header:
        logger.error("Missing X-CHEQROOM-Signature header")
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    if not verify_signature(body, signature_header):
        logger.error("Signature verification failed")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid signature")
    
    logger.info("✓ Signature verified successfully")
    
    # Parse JSON payload
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Validate required fields
    required_fields = ["updatedAt", "event", "item", "user"]
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {missing_fields}"
        )
    
    # Extract and validate data
    try:
        updated_at_str = data["updatedAt"]
        # Handle both ISO format with 'Z' and timezone-aware formats
        if updated_at_str.endswith("Z"):
            updated_at_str = updated_at_str.replace("Z", "+00:00")
        updated_at = datetime.fromisoformat(updated_at_str)
    except (ValueError, KeyError) as e:
        logger.error(f"Invalid timestamp format: {e}")
        raise HTTPException(status_code=400, detail="Invalid updatedAt format")
    
    event_type = data.get("event", "").lower()
    instrument_id = data.get("item", {}).get("id")
    
    if not instrument_id:
        logger.error("Missing instrument ID in webhook payload")
        raise HTTPException(status_code=400, detail="Missing instrument ID")
    
    user_info = {
        "f_name": data.get("user", {}).get("firstName", "Unknown"),
        "l_name": data.get("user", {}).get("lastName", "")
    }
    transaction_id = data.get("transaction_id")
    condition = data.get("condition")  # Optional
    
    logger.info(
        f"Webhook data extracted | Instrument: {instrument_id} | "
        f"Event: {event_type} | Timestamp: {updated_at}"
    )
    
    # ==========================================
    # PHASE 2 & 4: Process with row locking
    # ==========================================
    db = SessionLocal()
    try:
        # Phase 2: Timestamp comparison with row locking (FOR UPDATE in SQL)
        if not should_update_instrument(db, instrument_id, updated_at):
            db.rollback()
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "reason": "Incoming data is older than current DB record"
                }
            )
        
        # Phase 3 & 4: Process the update
        result = process_webhook_update(
            db,
            instrument_id,
            event_type,
            updated_at,
            user_info,
            transaction_id,
            condition
        )
        
        # Commit transaction
        db.commit()
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
    finally:
        db.close()


# ==========================================
# HEALTH CHECK ENDPOINT
# ==========================================

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "service": "cheqroom-webhook"}