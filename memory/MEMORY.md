# Email Intelligence Agent - Project Memory

## Project Context
- **Name**: Email Intelligence Agent for OHM
- **Type**: Autonomous AI-powered lifecycle marketing system
- **Stack**: Python 3.9+, OpenAI API, HubSpot/ConvertKit CRM
- **Purpose**: Autonomous email sequence writing, deployment, and optimization

## Architecture Overview
- **Modular design**: Agent, CRM, Integrations, Models, Analytics packages
- **CRM abstraction**: Supports both HubSpot and ConvertKit via base class pattern
- **OpenAI integration**: GPT-4 for email generation with brand voice guardrails
- **Webhook-driven**: Stripe and website behavior events trigger automations

## Key Security Rules
- **NEVER commit API keys** - Use .env.example as template, add .env to .gitignore
- **Environment variables only** - All credentials loaded from .env
- **Regenerate immediately** if keys are compromised (password manager or git history)
- **Stripe webhooks**: Must validate signatures with webhook secret

## Development Setup
- Virtual environment: `python -m venv venv`
- Install: `pip install -r requirements.txt`
- Config: Copy `.env.example` to `.env` and fill in API keys
- Run: `python -m src.main`

## Code Organization
- `src/config.py` - Handles all environment configuration with pydantic validation
- `src/integrations/openai_client.py` - OpenAI wrapper for email generation
- `src/crm/base.py` - Abstract base for CRM providers
- `src/models/email.py` - Email, Campaign, Analytics Pydantic models
- `src/main.py` - Entry point

## Testing & Quality
- Format: `black src/`
- Lint: `flake8 src/`
- Type check: `mypy src/`
- Tests: `pytest --cov=src tests/`

## Documentation Files
- **CLAUDE.md**: Development guide for Claude Code instances
- **README.md**: Quick start for new developers
- **OHM Brand Docs**: PDF/TXT files with brand voice and email sequences (20 emails total)

## Next Steps for Implementation
1. Implement HubSpot and ConvertKit clients (extend base CRM class)
2. Build email generator with prompt templates from OHM docs
3. Create webhook server for Stripe and behavior events
4. Implement A/B testing and analytics tracking
5. Add weekly optimization scheduler
6. Build churn recovery campaign logic
