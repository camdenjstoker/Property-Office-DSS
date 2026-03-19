# Quick Start Guide - Cheqroom Webhook Service

## 🚀 Get Started in 5 Minutes

### Option 1: Using Docker (Recommended)

**Prerequisites**: Docker and Docker Compose installed

```bash
# Navigate to webhook directory
cd webhook

# Copy environment template
cp .env.example .env

# Edit .env and set CHEQROOM_WEBHOOK_SECRET
# (Get this from Cheqroom dashboard)
nano .env  # or edit in your editor

# Start services (database + webhook)
docker-compose up -d

# Check service is running
curl http://localhost:8000/health

# View logs
docker-compose logs -f webhook
```

**Result**: Service runs at `http://localhost:8000`

### Option 2: Local Python Setup

**Prerequisites**: Python 3.8+, PostgreSQL running

```bash
# Navigate to webhook directory
cd webhook

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your database and webhook secret
nano .env

# (Optional) Initialize database
python setup_database.py

# Start the service
python main.py
```

**Result**: Service runs at `http://localhost:8000`

## 🔑 Configure Cheqroom Webhook

1. **Get Your Webhook Secret** from `.env` file (`CHEQROOM_WEBHOOK_SECRET`)

2. **Log in to Cheqroom Dashboard**

3. **Go to Settings → Webhooks**

4. **Create New Webhook**:
   - **Name**: "Property Office DSS"
   - **URL**: `https://your-domain.com/webhooks/cheqroom`
   - **Secret**: Paste your webhook secret
   - **Events**: Check "Check In" and "Check Out"
   - **Save**

## ✅ Test the Service

```bash
# Health check
curl http://localhost:8000/health

# You should see:
# {"status":"ok","service":"cheqroom-webhook"}

# Run tests
cd webhook
python test_webhook.py
```

## 📊 Monitor

**View Real-Time Logs**:
```bash
# Docker
docker-compose logs -f webhook

# Local
# Logs will appear in terminal where you ran `python main.py`
```

**Check Database Updates**:
```bash
psql -h localhost -U propoff -d propertyoffice

# In psql:
SELECT id, instrument_last_rented, instrument_last_returned 
FROM instrument WHERE id = 123;
```

## 🐛 Troubleshooting

### Service won't start
```bash
# Check database connection
psql -h localhost -U propoff -d propertyoffice -c "SELECT 1"

# Check environment variables
cat .env | grep -E "DB_|CHEQROOM"
```

### Database connection refused
```bash
# For Docker, ensure PostgreSQL is running
docker-compose ps

# For local install, start PostgreSQL separately
# (macOS with Homebrew):
brew services start postgresql
```

### Webhook signature invalid
```bash
# Verify secret in .env matches Cheqroom dashboard
echo $CHEQROOM_WEBHOOK_SECRET
# Should match what you see in Cheqroom dashboard
```

## 📁 File Structure

```
webhook/
├── app.py              ← Main webhook handler (Phase 1-4)
├── config.py           ← Configuration and settings
├── models.py           ← SQLAlchemy database models
├── main.py             ← Server entry point
├── setup_database.py   ← Database initialization
├── test_webhook.py     ← Test suite
├── requirements.txt    ← Dependencies
├── .env.example        ← Configuration template
├── Dockerfile          ← Docker image definition
├── docker-compose.yml  ← Docker Compose setup
└── README.md           ← Full documentation
```

## 🔄 How It Works

When Cheqroom sends a check-in/out event:

```
1. Webhook receives request → Phase 1: Verify signature
            ↓
2. Parse JSON payload → Phase 1: Validate data
            ↓
3. Extract timestamp → Phase 2: Compare with DB
            ↓
4. Check if newer → Discard if older, continue if newer
            ↓
5. Determine event type → Phase 3: Route to correct column
            ↓
6. Lock row and update → Phase 4: Update database
            ↓
7. Log transaction → Audit trail complete
```

## 📚 Next Steps

- Set up monitoring/alerting (see README.md)
- Configure database backups
- Set up HTTPS for production
- Monitor webhook logs regularly

## 🆘 Need Help?

See [README.md](README.md) for:
- Full API documentation
- Advanced configuration
- Performance tuning
- Security best practices
- Database schema details
