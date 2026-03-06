# Getting Started - Email Intelligence Agent

## Prerequisites

**System Requirements:**
- Python 3.9 or higher
- `uv` (fast Python package manager) - https://github.com/astral-sh/uv
- Git (for version control)
- ~500MB disk space (for dependencies + SQLite DB)

**Install uv:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip as fallback
pip install uv
```

**Required API Keys:**
1. **OpenAI API Key** - for email generation
2. **CRM Choice** - HubSpot OR ConvertKit API credentials
3. **Stripe API Key + Webhook Secret** (optional, for automation)

---

## 1. Installation

### Step 1: Clone or Navigate to Project

```bash
# Navigate to project directory
cd "C:\Users\Nisar\Desktop\AI Email Agent_OHM (05 March 2026)"

# Verify you see the src/ and tests/ directories
ls
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies with uv

**IMPORTANT: Always use `uv` for dependency management. Never use `pip` directly.**

```bash
# Install all dependencies from requirements.txt using uv
uv pip install -r requirements.txt

# View installed packages
uv pip list
```

**Why requirements.txt?** Ensures all team members have identical dependency versions.

**Optional: Install development tools**
```bash
# Install development dependencies (testing, linting, formatting)
uv pip install -r requirements-dev.txt
```

**Why uv?**
- ✓ 10-100x faster than pip
- ✓ Better dependency resolution
- ✓ Lower memory usage
- ✓ Modern standard for Python

See `UV_DEPENDENCY_MANAGEMENT.md` for comprehensive dependency management guide.

---

## 2. Configuration

### Step 1: Create .env File

Create a `.env` file in the project root:

```bash
# From project directory
touch .env
```

### Step 2: Copy Template and Fill in Credentials

**Minimum Configuration (Required):**

```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-your-api-key-here
OPENAI_MODEL=gpt-4

# CRM Configuration - Choose ONE
CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=pat-your-hubspot-key-here

# OR use ConvertKit:
# CRM_PROVIDER=convertkit
# CONVERTKIT_API_KEY=your-convertkit-key-here

# Email Configuration
SENDER_EMAIL=no-reply@ohm.com
SENDER_NAME=OHM Team

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./email_agent.db

# Server
WEBHOOK_PORT=8000
```

**With Stripe Webhooks (Optional):**

```env
# Add these for webhook automation
STRIPE_API_KEY=sk_test_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
```

### Step 3: Get Your API Keys

#### **OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy and paste into `.env`

#### **HubSpot API Key:**
1. Go to https://app.hubspot.com/l/api-key/
2. Create private app or get API key
3. Copy to `.env`

#### **ConvertKit API Key:**
1. Go to https://app.convertkit.com/account/settings
2. Find API Key in settings
3. Copy to `.env`

#### **Stripe Webhook Secret:**
1. Go to https://dashboard.stripe.com/webhooks
2. Create webhook endpoint: `https://yourdomain.com/webhooks/stripe`
3. Copy signing secret to `.env`

### Step 4: Verify Configuration

```bash
# Test that imports work
python -c "from src.config import settings; print('✓ Config loaded successfully')"
```

---

## 3. Running the Application

### Option A: Run Main Agent (Development)

```bash
# Activate venv first (if not already)
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the agent
python -m src.main
```

**Expected Output:**
```
2026-03-05 10:30:00 - src.main - INFO - Initializing Email Intelligence Agent (environment: development)
2026-03-05 10:30:01 - src.main - INFO - Initialized hubspot CRM client
2026-03-05 10:30:01 - src.main - INFO - Initialized OpenAI client
2026-03-05 10:30:01 - src.main - INFO - Initialized email generator
2026-03-05 10:30:01 - src.main - INFO - Initialized audience segmentor
2026-03-05 10:30:01 - src.main - INFO - Initialized campaign optimizer
2026-03-05 10:30:01 - src.main - INFO - Initialized email tracker
2026-03-05 10:30:01 - src.main - INFO - Initialized analytics reporter
2026-03-05 10:30:01 - src.main - INFO - Initialized Stripe webhook handler
2026-03-05 10:30:01 - src.main - INFO - Email Intelligence Agent ready
2026-03-05 10:30:01 - src.main - INFO - Segmented 150 contacts across 7 segments
2026-03-05 10:30:01 - src.main - INFO - Agent initialized and ready to handle webhooks
```

### Option B: Run with Webhook Server

```bash
# Activate venv
source venv/bin/activate

# Run with async webhook server (requires asyncio)
python -c "
import asyncio
from src.main import EmailIntelligenceAgent

async def main():
    agent = EmailIntelligenceAgent()
    await agent.start_webhook_server()

asyncio.run(main())
"
```

Webhook server will run at `http://localhost:8000`

### Option C: Interactive Testing

```bash
# Start Python REPL
python

# Inside Python:
from src.main import EmailIntelligenceAgent

# Initialize agent
agent = EmailIntelligenceAgent()

# Segment contacts
segments = agent.run_segmentation()
print(f"Segments: {list(segments.keys())}")

# Generate campaign
emails = agent.generate_campaign_sequence(
    segment="cold_prospect",
    campaign_type="cold_outbound",
    recipient_count=5  # Small test batch
)
print(f"Generated {len(emails)} emails")

# Get weekly report
report = agent.get_weekly_report()
print(f"Weekly report: {report.total_emails_sent} sent, {report.avg_open_rate:.1%} avg open")

# Exit
exit()
```

---

## 4. Testing

### Run Unit Tests

```bash
# Activate venv
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/agent/test_email_generator.py

# Run specific test
pytest tests/agent/test_email_generator.py::test_guardrail_validation -v
```

### Run Quick Validation

```bash
python << 'EOF'
# Quick validation script
from src.config import settings
from src.agent.email_generator import EmailGenerator

print("✓ Configuration loaded")

# Test guardrail validation
gen = EmailGenerator()
print("✓ Email generator initialized")

# Test guardrail (should fail)
bad_email = "This medical device treats depression and offers a money-back guarantee."
result = gen.validate_against_guardrails(bad_email)
print(f"✓ Guardrail validation works (result for bad email: {result})")

# Test good email (should pass)
good_email = "Join our digital-first spiritual platform for conscious evolution and renewal."
result = gen.validate_against_guardrails(good_email)
print(f"✓ Good email validation (result: {result})")

print("\n✅ All basic validations passed!")
EOF
```

---

## 5. Working with Different CRM Providers

### Using HubSpot

```bash
# .env configuration
CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=pat_your_key_here

# Test connection
python << 'EOF'
from src.crm.hubspot_client import HubSpotClient

client = HubSpotClient()
contacts = client.get_contacts(limit=5)
print(f"✓ Connected to HubSpot, retrieved {len(contacts)} contacts")
EOF
```

### Using ConvertKit

```bash
# .env configuration
CRM_PROVIDER=convertkit
CONVERTKIT_API_KEY=your_key_here

# Test connection
python << 'EOF'
from src.crm.convertkit_client import ConvertKitClient

client = ConvertKitClient()
contacts = client.get_contacts(limit=5)
print(f"✓ Connected to ConvertKit, retrieved {len(contacts)} subscribers")
EOF
```

---

## 6. Webhook Testing (Stripe)

### Start Webhook Server

```bash
# Terminal 1: Start the webhook server
python << 'EOF'
import asyncio
from src.main import EmailIntelligenceAgent

async def main():
    agent = EmailIntelligenceAgent()
    print("Starting webhook server on http://localhost:8000")
    await agent.start_webhook_server()

asyncio.run(main())
EOF
```

### Test with Sample Webhook

```bash
# Terminal 2: Send test webhook event
python << 'EOF'
import requests
import json
import hmac
import hashlib
import time

# Simulate Stripe webhook
event = {
    "id": "evt_test_123",
    "type": "customer.subscription.created",
    "created": int(time.time()),
    "data": {
        "object": {
            "id": "sub_test_123",
            "customer": "cus_test_123",
            "items": {
                "data": [{
                    "product": "prod_phoenix"
                }]
            }
        }
    }
}

payload = json.dumps(event).encode()

# Generate signature (requires STRIPE_WEBHOOK_SECRET from .env)
secret = "whsec_test_secret"  # Use actual secret from .env
timestamp = str(int(time.time()))
signed_content = f"{timestamp}.{payload.decode()}"
signature = hmac.new(
    secret.encode(),
    signed_content.encode(),
    hashlib.sha256
).hexdigest()
sig_header = f"t={timestamp},v1={signature}"

# Send to webhook
response = requests.post(
    "http://localhost:8000/webhooks/stripe",
    data=payload,
    headers={
        "Stripe-Signature": sig_header,
        "Content-Type": "application/json"
    }
)

print(f"Webhook response: {response.status_code}")
print(f"Response: {response.json()}")
EOF
```

---

## 7. Common Issues & Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution:**
```bash
# Make sure you're in the project root directory
pwd  # or cd on Windows

# Check that src/ directory exists
ls src/

# Reinstall in development mode using uv
uv pip install -e .
```

### Issue: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Verify .env file exists in project root
ls -la | grep .env

# Verify it has the key
cat .env | grep OPENAI_API_KEY

# Check .env syntax (no quotes around values)
# ✓ Correct: OPENAI_API_KEY=sk-proj-...
# ✗ Wrong: OPENAI_API_KEY="sk-proj-..."
```

### Issue: "CRMError: HUBSPOT_API_KEY not configured"

**Solution:**
```bash
# Make sure CRM_PROVIDER matches your credentials
# If using HubSpot, ensure:
CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=pat_...

# If using ConvertKit, ensure:
CRM_PROVIDER=convertkit
CONVERTKIT_API_KEY=...

# Reload environment
python -m src.main
```

### Issue: "WebhookValidationError: Invalid webhook signature"

**Solution:**
```bash
# Verify your STRIPE_WEBHOOK_SECRET is correct
# Get from: https://dashboard.stripe.com/webhooks

# Verify signature timestamp (must be within 5 minutes)
# Check system clock is correct: date

# For testing, use Stripe CLI:
# brew install stripe/stripe-cli/stripe
# stripe listen --forward-to localhost:8000/webhooks/stripe
```

### Issue: "sqlite3.OperationalError: database is locked"

**Solution:**
```bash
# SQLite lock from another process
# Kill any running Python processes:
pkill -f "python.*src.main"

# Or delete and recreate database:
rm email_agent.db
python -m src.main
```

### Issue: "OpenAI API rate limit exceeded"

**Solution:**
```bash
# Wait before retrying (rate limit is per minute)
# Or upgrade your OpenAI plan: https://platform.openai.com/account/billing/overview

# Reduce test batch size:
emails = agent.generate_campaign_sequence(
    segment="cold_prospect",
    campaign_type="cold_outbound",
    recipient_count=1  # Test with 1 instead of 100
)
```

---

## 8. Development Workflow

### Making Changes to Code

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Make your changes in src/

# 3. Test immediately
pytest tests/

# 4. Run the agent to verify
python -m src.main

# 5. Check code quality
flake8 src/  # Lint
mypy src/    # Type checking (if available)
black src/   # Format (if available)
```

### Adding New Features

Example: Adding a new email campaign type

```bash
# 1. Add campaign to src/prompts/email_sequences.yaml
# 2. Update src/agent/email_generator.py to handle new type
# 3. Write tests in tests/agent/test_email_generator.py
# 4. Run tests: pytest tests/agent/
# 5. Test manually with agent.generate_campaign_sequence()
```

### Debugging

```bash
# Enable verbose logging
# In .env:
LOG_LEVEL=DEBUG

# Or in code:
import logging
logging.basicConfig(level=logging.DEBUG)

# Add print statements and run
python -m src.main
```

---

## 9. Production Deployment Checklist

Before deploying to production:

- [ ] `.env` contains all required credentials
- [ ] `ENVIRONMENT=production` in `.env`
- [ ] Database backed up (use external DB, not SQLite)
- [ ] OpenAI API key has usage limits configured
- [ ] CRM API credentials tested and working
- [ ] Stripe webhook secret configured correctly
- [ ] HTTPS enabled for webhook endpoint
- [ ] Logging aggregated (CloudWatch, Datadog, etc.)
- [ ] Error monitoring enabled (Sentry, etc.)
- [ ] Rate limiting configured on webhook endpoint
- [ ] Database connection pooling configured
- [ ] All tests passing: `pytest --cov=src`

---

## 10. Key Files & Directories

```
C:\Users\Nisar\Desktop\AI Email Agent_OHM (05 March 2026)\
├── .env                          # Configuration (create this)
├── src/
│   ├── main.py                   # Entry point - START HERE
│   ├── config.py                 # Environment settings
│   ├── agent/
│   │   ├── email_generator.py    # Email generation
│   │   ├── segmentation.py       # Audience segmentation
│   │   └── optimizer.py          # A/B testing
│   ├── crm/
│   │   ├── base.py               # Abstract interface
│   │   ├── hubspot_client.py     # HubSpot integration
│   │   └── convertkit_client.py  # ConvertKit integration
│   ├── integrations/
│   │   ├── openai_client.py      # OpenAI wrapper
│   │   └── stripe_webhook.py     # Stripe webhooks
│   ├── analytics/
│   │   ├── tracker.py            # Event tracking
│   │   └── reporter.py           # Analytics reports
│   ├── models/                   # Pydantic data models
│   └── prompts/
│       ├── guardrails.yaml       # Brand voice rules
│       └── email_sequences.yaml  # Email templates
├── tests/                        # Test files
├── CLAUDE.md                     # Project guidelines
├── SPECIFICATION.md              # Technical spec
├── CODEBASE_OVERVIEW.md          # Architecture
├── ARCHITECTURE_DIAGRAMS.md      # Flow diagrams
└── GETTING_STARTED.md            # This file
```

---

## 11. Quick Commands Reference

```bash
# Setup (using uv for all dependency management)
python -m venv venv
source venv/bin/activate
uv pip install -r requirements.txt

# Create .env (edit with your credentials)
touch .env

# Run
python -m src.main

# Test
pytest
pytest --cov=src tests/

# Debug
python -c "from src.config import settings; print(settings)"

# Interactive
python
>>> from src.main import EmailIntelligenceAgent
>>> agent = EmailIntelligenceAgent()
>>> exit()
```

---

## 12. Next Steps

1. **Create `.env` file** with your API keys
2. **Run `python -m src.main`** to initialize agent
3. **Check logs** for any configuration errors
4. **Run tests** with `pytest`
5. **Try example commands** from "Interactive Testing" section
6. **Read CODEBASE_OVERVIEW.md** to understand architecture
7. **Read SPECIFICATION.md** for detailed requirements

---

## Support & Debugging

**Check the logs:**
```bash
# Logs print to console when you run the agent
python -m src.main

# For file logging, update config.py to add file handler
```

**Verify configuration:**
```bash
python << 'EOF'
from src.config import settings
print(f"CRM Provider: {settings.crm_provider}")
print(f"OpenAI Model: {settings.openai_model}")
print(f"Database: {settings.database_url}")
print(f"Environment: {settings.environment}")
print(f"Webhook Port: {settings.webhook_port}")
EOF
```

**Test each component:**
```bash
# Test CRM
python -c "from src.crm.hubspot_client import HubSpotClient; print('✓ HubSpot OK')"

# Test OpenAI
python -c "from src.integrations.openai_client import EmailGenerationClient; print('✓ OpenAI OK')"

# Test Email Generator
python -c "from src.agent.email_generator import EmailGenerator; print('✓ Generator OK')"

# Test all imports
python -m src.main
```

**Issues? Check:**
- `.env` file syntax (no quotes, proper format)
- API key validity (test in provider's dashboard)
- Python 3.9+ installed (`python --version`)
- Virtual environment activated (see `(venv)` in prompt)
- All dependencies installed (`uv pip list`)
