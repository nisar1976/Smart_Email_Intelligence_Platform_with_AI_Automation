# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Email Intelligence Agent** - A fully autonomous lifecycle marketing agent for OHM that writes, deploys, and optimizes email sequences using AI.

### Core Features
- Autonomous email sequence generation and deployment
- Behavioral audience segmentation
- Email performance analytics (open rates, CTR, conversion tracking)
- A/B testing automation
- Weekly subject line optimization
- Upsell funnel automation (Phoenix → Visionary → Infinity)
- Churned member reactivation campaigns

### Tech Stack
- **LLM**: OpenAI API (GPT-4/GPT-3.5-turbo)
- **CRM**: HubSpot or ConvertKit integration
- **Data Source**: Webhooks from Stripe + website behavior tracking
- **Language**: Python 3.9+
- **Async Support**: For webhook handling and API calls

## Architecture

### Module Structure
```
src/
├── agent/                    # Core agent logic
│   ├── email_generator.py   # Email sequence generation with OpenAI
│   ├── segmentation.py      # Audience behavioral segmentation
│   └── optimizer.py         # A/B testing and optimization logic
├── crm/                      # CRM integrations
│   ├── hubspot_client.py    # HubSpot API wrapper
│   └── convertkit_client.py # ConvertKit API wrapper
├── integrations/             # External service integrations
│   ├── stripe_webhook.py    # Stripe webhook handling
│   └── openai_client.py     # OpenAI API wrapper with prompt templates
├── models/                   # Data models and schemas
│   ├── email.py             # Email data models
│   ├── campaign.py          # Campaign data models
│   └── analytics.py         # Analytics data models
├── analytics/                # Performance tracking
│   ├── tracker.py           # Email open/click tracking
│   └── reporter.py          # Analytics reporting
├── prompts/                  # AI prompt templates
│   ├── email_sequences.yaml # 20-email sequence templates
│   └── guardrails.yaml      # Brand voice guardrails
└── config.py                # Configuration and environment handling
```

### Key Design Patterns

1. **Prompt Library System**: Prompts trained on THE COMPLETE 20-EMAIL OHM SALES SEQUENCE.pdf are stored in `src/prompts/`. Guardrails from OHM BRAND VOICE AI TRAINING GUIDE.pdf enforce brand consistency.

2. **CRM Abstraction**: Abstract base class for CRM operations allows switching between HubSpot and ConvertKit without changing core logic.

3. **Webhook Handler**: Receives Stripe and website behavior events, triggers automation rules (e.g., upsell campaigns after purchase).

4. **Analytics Pipeline**: Tracks email metrics (open, click, conversion) and triggers optimization routines weekly.

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and configure with your API keys
cp .env.example .env
```

### Code Quality
```bash
# Format code
black src/

# Lint
flake8 src/

# Type checking
mypy src/

# Run all checks
black src/ && flake8 src/ && mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/agent/test_email_generator.py

# Run tests matching pattern
pytest -k "test_segmentation"
```

### Running the Agent
```bash
# Start the agent (runs webhook server and background tasks)
python -m src.main

# Run a specific campaign
python -m src.agent.email_generator --campaign-name "Phoenix Sequence"
```

## Important Notes

### Security & Credentials
- **Never commit `.env` files** - API keys, database URLs, and webhook secrets are environment-specific
- Use `.env.example` as a template for required variables
- All credentials must be loaded from environment variables, never hardcoded
- GitHub Actions and CI/CD should use repository secrets, not .env files

### API Key Management
- Regenerate compromised API keys immediately in provider dashboards
- OpenAI keys should have organization/project restrictions where possible
- Stripe webhook secrets are sensitive—treat like passwords
- HubSpot/ConvertKit tokens should be rotated periodically

### Brand Voice Consistency
- All generated emails must be validated against guardrails in `src/prompts/guardrails.yaml`
- Weekly human review is required before deployment to production
- Guardrail violations should be logged and escalated for manual review

### CRM Integration Notes
- **HubSpot**: Use OAuth2 for production deployments, not API keys
- **ConvertKit**: API is read-heavy; batch operations where possible
- Webhook payload validation is critical to prevent unauthorized triggers

### Analytics & Optimization
- A/B test results require statistical significance before implementation
- Weekly optimization runs should be logged with before/after metrics
- Churned member reactivation campaigns use different templates than new user sequences

### Webhook Handling
- Stripe webhooks trigger email automation (purchase → upsell sequence)
- Website behavior webhooks should be deduplicated (same event within 5 minutes = single trigger)
- All webhook handlers must be idempotent (safe to replay)

## Documentation References
- **OHM Brand Knowledge**: `OHM — Full Brand Knowledge & Messaging Framework.txt`
- **Brand Voice Guardrails**: `OHM BRAND VOICE AI TRAINING GUIDE.pdf`
- **Email Sequences**: `THE COMPLETE 20-EMAIL OHM SALES SEQUENCE.pdf`
- **Service Knowledge**: `OHM Signature Service Knowledge Base.pdf`
