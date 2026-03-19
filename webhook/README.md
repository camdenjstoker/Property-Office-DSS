# Cheqroom Webhook Service

Real-time "Check-in/out" updates with instant database synchronization, HMAC signature verification, and race condition prevention.

## Overview

This webhook service receives real-time events from Cheqroom and updates the Property-Office-DSS database with instrument check-in/check-out information. It implements four critical phases:

### 🟢 Phase 1: The "Receptionist" Endpoint
Secure POST endpoint that receives and validates Cheqroom webhook signals.
- **Route**: `POST /webhooks/cheqroom`
- **Security**: HMAC-SHA256 signature verification via `X-CHEQROOM-Signature` header
- **Validation**: Returns 401 Unauthorized if signatures don't match

### 🟡 Phase 2: The "Newer-Wins" Logic
Prevents race conditions between webhook updates and scheduled tasks.
- Extracts `updatedAt` timestamp from Cheqroom payload
- Compares to existing `instrument_last_rented` and `instrument_last_returned` in database
- Discards updates if incoming data is older than current DB record
- Proceeds only if incoming data is newer

### 🔵 Phase 3: Check-in/Check-out Branching
Routes events to appropriate database columns based on user action.
- **"Checked Out"** → Updates `instrument_last_rented` column
- **"Checked In"** → Updates `instrument_last_returned` column
- Maintains audit log with transaction ID and user information

### 🟣 Phase 4: Combined Endpoint Logic
Unified processing with row locking to prevent simultaneous write errors.
- Uses SQLAlchemy `with_for_update()` (SQL `FOR UPDATE` clause)
- Locks specific row during update
- Ensures data consistency during concurrent operations

## Project Structure

```
webhook/
├── app.py                    # Main FastAPI application with all 4 phases
├── models.py                 # SQLAlchemy ORM models
├── config.py                 # Configuration management
├── main.py                   # Server entry point
├── test_webhook.py           # Comprehensive test suite
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── __init__.py               # Package initialization
└── README.md                 # This file
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your values
# CRITICAL: Set CHEQROOM_WEBHOOK_SECRET to match your Cheqroom dashboard
```

### 3. Prepare Database

The webhook service requires the following columns in the `instrument` table:
- `instrument_last_rented` (DateTime)
- `instrument_last_returned` (DateTime)
- `instrument_condition` (String) - optional, for condition updates

Create the audit log table (optional but recommended):

```sql
CREATE TABLE IF NOT EXISTS public.webhook_audit_log (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL,
    event_type VARCHAR(50),
    user_name VARCHAR(500),
    transaction_id VARCHAR(255),
    timestamp_from_cheqroom TIMESTAMP,
    timestamp_processed TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Running the Service

### Option 1: Using main.py

```bash
python main.py
```

### Option 2: Direct Uvicorn

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Production with Gunicorn

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

The service will start on `http://0.0.0.0:8000` by default.

## Testing

Run the comprehensive test suite:

```bash
python test_webhook.py
```

Or with pytest:

```bash
pytest test_webhook.py -v
```

### Test Coverage

The test suite validates:

**Phase 1 - Signature Verification:**
- ✓ Valid signature accepted
- ✓ Missing signature returns 401
- ✓ Invalid signature returns 401
- ✓ Wrong secret rejected

**Phase 1 - Payload Validation:**
- ✓ Missing required fields rejected
- ✓ Invalid timestamp format rejected
- ✓ Missing instrument ID rejected

**Phase 3 - Event Processing:**
- ✓ Checked-out events processed correctly
- ✓ Checked-in events processed correctly
- ✓ Unknown event types handled

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |
| `API_DEBUG` | `false` | Enable debug mode and reload |
| `DB_USER` | `propoff` | PostgreSQL user |
| `DB_PASSWORD` | `student` | PostgreSQL password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `propertyoffice` | Database name |
| `DB_SCHEMA` | `public` | Database schema |
| `CHEQROOM_WEBHOOK_SECRET` | (required) | Secret from Cheqroom dashboard |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Maximum overflow connections |

## API Endpoints

### POST /webhooks/cheqroom

Receives webhook payload from Cheqroom.

**Headers:**
```
X-CHEQROOM-Signature: <HMAC-SHA256 signature>
Content-Type: application/json
```

**Request Body:**
```json
{
  "updatedAt": "2024-03-11T14:30:45Z",
  "event": "checked_out",
  "item": {
    "id": 123,
    "name": "Violin"
  },
  "user": {
    "firstName": "John",
    "lastName": "Doe"
  },
  "transaction_id": "tx-abc123",
  "condition": "good"
}
```

**Success Response (200):**
```json
{
  "status": "updated",
  "action": "checked_out",
  "instrument_id": 123,
  "user": "John Doe",
  "timestamp": "2024-03-11T14:30:45Z"
}
```

**Ignored Response (200) - Older Data:**
```json
{
  "status": "ignored",
  "reason": "Incoming data is older than current DB record"
}
```

**Error Response (401 - Invalid Signature):**
```json
{
  "detail": "Unauthorized: Invalid signature"
}
```

**Error Response (400 - Invalid Payload):**
```json
{
  "detail": "Missing required fields: [...]"
}
```

### GET /health

Health check endpoint.

**Response (200):**
```json
{
  "status": "ok",
  "service": "cheqroom-webhook"
}
```

## Cheqroom Configuration

### Setting up the Webhook in Cheqroom

1. Log in to Cheqroom dashboard
2. Navigate to **Settings** → **Webhooks** or **Integrations**
3. Create a new webhook:
   - **Name**: "Property Office DSS"
   - **URL**: `https://your-domain.com/webhooks/cheqroom`
   - **Method**: `POST`
   - **Events**: Select "Check In" and "Check Out"
   - **Secret**: Copy the generated secret to `CHEQROOM_WEBHOOK_SECRET` environment variable

### Webhook Payload Format

Cheqroom sends JSON payloads with this structure:

```json
{
  "event": "checked_out|checked_in",
  "updatedAt": "2024-03-11T14:30:45Z",
  "item": {
    "id": <number>,
    "name": "<string>",
    "barcode": "<string>"
  },
  "user": {
    "firstName": "<string>",
    "lastName": "<string>"
  },
  "transaction_id": "<string>"
}
```

## Database Schema

### Instrument Table (Required Columns)

```sql
CREATE TABLE public.instrument (
    id SERIAL PRIMARY KEY,
    instrument_type VARCHAR(255),
    instrument_barcode VARCHAR(255) UNIQUE,
    instrument_condition VARCHAR(50),
    instrument_last_rented TIMESTAMP,
    instrument_last_returned TIMESTAMP,
    -- ... other columns ...
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Webhook Audit Log (Optional)

Recommended for tracking all webhook transactions:

```sql
CREATE TABLE public.webhook_audit_log (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL,
    event_type VARCHAR(50),
    user_name VARCHAR(500),
    transaction_id VARCHAR(255),
    timestamp_from_cheqroom TIMESTAMP,
    timestamp_processed TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (instrument_id) REFERENCES public.instrument(id)
);
```

## Advanced Features

### Row Locking

The service uses SQLAlchemy's `with_for_update()` (SQL `FOR UPDATE`) to implement optimistic locking:

```sql
SELECT ... FROM instrument WHERE id = :id FOR UPDATE
```

This ensures:
- Only one transaction can update a row at a time
- Other transactions wait for the lock to be released
- Prevents race conditions and data inconsistency

### Audit Logging

All webhook transactions are logged with:
- Instrument ID
- Event type (check-in/out)
- User name
- Transaction ID from Cheqroom
- Timestamps (Cheqroom time vs. processed time)
- Status (success/ignored/error)

Access logs:
```bash
# View recent logs
tail -f /var/log/webhook-service.log

# Or in the console where the service runs
```

## Troubleshooting

### Signature Verification Failed

**Problem**: Webhook returns 401 Unauthorized

**Solution**:
1. Verify `CHEQROOM_WEBHOOK_SECRET` matches Cheqroom dashboard
2. Check logs for signature mismatch details
3. Ensure POST body is not being modified in transit

### Timestamp Comparison Issues

**Problem**: Legitimate updates are being ignored

**Check**:
1. Verify Cheqroom and server timezones are compatible
2. Ensure database timestamps are stored in UTC
3. Check for timezone conversion issues

### Database Connection Failed

**Problem**: Service won't start or updates fail with connection error

**Solution**:
1. Verify database credentials in `.env`
2. Test connection manually: `psql -h localhost -U propoff -d propertyoffice`
3. Check network connectivity to database host
4. Verify database is running

### Row Lock Timeout

**Problem**: Updates fail with "deadlock detected"

**Mitigation**:
1. Increase `DB_POOL_SIZE` to allow more concurrent connections
2. Add retry logic for transient lock timeouts
3. Consider using connection pooling (PgBouncer)

## Performance Considerations

- **Connection Pooling**: Default pool size is 5 connections. Adjust `DB_POOL_SIZE` based on expected webhook volume.
- **Batch Processing**: The service processes one webhook at a time. For high-volume scenarios, consider async processing.
- **Database Indexes**: Ensure indexes exist on instrument ID for fast lookups:
  ```sql
  CREATE INDEX idx_instrument_id ON public.instrument(id);
  ```

## Security Best Practices

1. **Environment Variables**: Always use `.env` files, never hardcode secrets
2. **Signature Verification**: Always verify webhook signatures before processing
3. **HTTPS**: Always use HTTPS in production (set up reverse proxy like Nginx)
4. **IP Whitelisting**: Consider whitelisting Cheqroom's IP addresses (contact Cheqroom support)
5. **Rate Limiting**: Implement rate limiting for production deployments
6. **Logging**: Don't log sensitive data (passwords, full signatures)

## Integration with Property-Office-DSS

### Integration Points

1. **ETL Script** (`sql_script.py`): Bulk synchronization on startup
2. **Webhook Service** (`webhook/app.py`): Real-time updates during operation
3. **Database**: Shared `instrument`, `books`, `accessory`, `locker`, `user`, `financial` tables

### Workflow

```
Cheqroom (Source)
      ↓
   Webhook
      ↓
   Signature Verification (Phase 1)
      ↓
   Timestamp Comparison (Phase 2)
      ↓
   Event Routing (Phase 3)
      ↓
   Row Locking & Update (Phase 4)
      ↓
Property-Office-DSS Database
```

## Future Enhancements

- [ ] Implement audit log storage in `webhook_audit_log` table
- [ ] Add retry logic for failed updates
- [ ] Implement exponential backoff for transient errors
- [ ] Add Cheqroom API integration for condition updates
- [ ] Create admin dashboard for webhook monitoring
- [ ] Add alerting for failed webhooks
- [ ] Implement webhook signature rotation

## Support & Debugging

### Enable Debug Logging

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in .env
LOG_LEVEL=DEBUG

# Restart service
python main.py
```

### View SQL Queries

```python
# In config.py, change:
echo=False  # → echo=True
```

### Test Webhook Manually

```bash
curl -X POST http://localhost:8000/webhooks/cheqroom \
  -H "Content-Type: application/json" \
  -H "X-CHEQROOM-Signature: <signature>" \
  -d '{"updatedAt":"2024-03-11T14:30:45Z",...}'
```

## License

Part of Property-Office-DSS project

## Last Updated

March 2024
