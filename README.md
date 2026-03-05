# Email Intelligence Agent for OHM

An autonomous AI-powered system for lifecycle marketing that writes, deploys, and optimizes email sequences for the OHM brand.

## Quick Start

### Setup
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Configure
Edit `.env` with your API keys:
- `OPENAI_API_KEY` - Your OpenAI API key
- `HUBSPOT_API_KEY` or `CONVERTKIT_API_KEY` - Your CRM credentials
- `STRIPE_API_KEY` and `STRIPE_WEBHOOK_SECRET` - For payment webhooks

### Run
```bash
python -m src.main
```

## Key Features

✅ **Autonomous Email Generation** - Uses OpenAI GPT-4 to write sequences
✅ **Behavioral Segmentation** - Targets users by engagement & purchase history
✅ **Performance Analytics** - Tracks opens, clicks, conversions
✅ **A/B Testing** - Automatically tests subject lines & content
✅ **Upsell Automation** - Triggers Phoenix → Visionary → Infinity sequences
✅ **Churn Recovery** - Reactivates inactive members
✅ **Brand Voice Guardrails** - Enforces OHM messaging standards

## Development

See [CLAUDE.md](./CLAUDE.md) for comprehensive development documentation.

### Code Quality
```bash
black src/ && flake8 src/ && mypy src/
```

### Testing
```bash
pytest --cov=src tests/
```

## Project Structure

```
src/
├── agent/           # Core email generation & optimization
├── crm/             # CRM integrations (HubSpot, ConvertKit)
├── integrations/    # External APIs (OpenAI, Stripe)
├── models/          # Data models (Email, Campaign, Analytics)
├── analytics/       # Performance tracking & reporting
└── prompts/         # AI prompt templates & guardrails
```

## Documentation

- **Brand & Messaging**: `OHM — Full Brand Knowledge & Messaging Framework.txt`
- **Brand Voice Guide**: `OHM BRAND VOICE AI TRAINING GUIDE.pdf`
- **Email Sequences**: `THE COMPLETE 20-EMAIL OHM SALES SEQUENCE.pdf`
- **Service Knowledge**: `OHM Signature Service Knowledge Base.pdf`

## ⚠️ Security

- **Never commit `.env` files** - Contains sensitive credentials
- **Rotate API keys** if compromised
- All credentials must be environment variables, never hardcoded
- Webhook handlers are idempotent and validate all payloads

## License

Internal OHM project - All rights reserved.
