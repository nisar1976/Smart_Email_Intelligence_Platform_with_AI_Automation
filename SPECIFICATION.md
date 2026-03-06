# Specification: Email Intelligence Agent for OHM

## Context

This spec formalizes the build requirements for the OHM Email Intelligence Agent, a fully autonomous lifecycle marketing system. The agent must operate within OHM's brand voice guardrails (from OHM brand docs), use OpenAI GPT-4 for email generation, integrate with HubSpot/ConvertKit for CRM operations, and automate the full email lifecycle—from generation to delivery, tracking, A/B testing, optimization, upsell triggers, and churn recovery.

The project skeleton exists (`src/config.py`, `src/crm/base.py`, `src/integrations/openai_client.py`, `src/models/email.py`). This spec covers what each module must implement.

---

## 1. Module Specifications

### 1.1 `src/agent/email_generator.py`

**Purpose**: Orchestrates email generation using the OpenAI client + prompt library.

**Class: `EmailGenerator`**
- `generate_sequence(segment: str, campaign_type: str) -> List[Email]`
  - Generates a full sequence (up to 20 emails) for a given audience segment
  - Selects the correct prompt template from `src/prompts/email_sequences.yaml`
  - Injects guardrails from `src/prompts/guardrails.yaml`
  - Returns a list of `Email` Pydantic objects (defined in `src/models/email.py`)
- `generate_single_email(segment: str, step: int, context: dict) -> Email`
  - Calls `EmailGenerationClient.generate_email()` in `src/integrations/openai_client.py`
  - Validates output against brand guardrails before returning
  - Raises `GuardrailViolationError` if output fails brand compliance check
- `validate_against_guardrails(email_content: str) -> bool`
  - Uses a second OpenAI call to check compliance with OHM brand rules
  - Checks: no medical claims, no religious org framing, no therapy/clinical language
  - Logs violations for human review

**Campaign Types** (maps to segment + funnel stage):
- `"onboarding"` — new Phoenix member welcome sequence
- `"upsell_phoenix_visionary"` — Phoenix → Visionary upgrade
- `"upsell_visionary_infinity"` — Visionary → Infinity upgrade
- `"reactivation"` — churned member win-back
- `"cold_outbound"` — cold prospect acquisition

---

### 1.2 `src/agent/segmentation.py`

**Purpose**: Classifies contacts into behavioral segments based on CRM + Stripe data.

**Class: `AudienceSegmentor`**
- `segment_all(crm_client: CRMClient) -> Dict[str, List[str]]`
  - Returns a dict mapping segment name → list of contact IDs
  - Segments defined below
- `classify_contact(contact: dict, stripe_data: dict) -> str`
  - Returns the best-fit segment for a single contact

**Segment Definitions:**
| Segment | Criteria |
|---|---|
| `cold_prospect` | No purchase, no engagement in 30+ days |
| `new_phoenix` | Subscribed Phoenix tier < 7 days ago |
| `active_phoenix` | Phoenix, engaged in last 14 days, no upsell yet |
| `upsell_candidate_visionary` | Active Phoenix, 30+ days, clicked upsell CTA |
| `upsell_candidate_infinity` | Active Visionary, 30+ days, clicked upsell CTA |
| `churned` | Cancelled subscription or no login in 60+ days |
| `reactivation` | Churned > 90 days, previously active |

---

### 1.3 `src/agent/optimizer.py`

**Purpose**: A/B testing and weekly subject line optimization.

**Class: `CampaignOptimizer`**
- `create_ab_test(campaign: EmailCampaign, variant_b_subject: str) -> Tuple[EmailCampaign, EmailCampaign]`
  - Splits campaign recipients 50/50 into variant A and B
  - Variant B uses the alternative subject line
  - Returns two campaign objects with `is_abtest=True`
- `evaluate_ab_test(campaign_a_id: str, campaign_b_id: str, crm: CRMClient) -> str`
  - Compares open rates; returns winning campaign ID
  - Requires minimum 100 recipients per variant and 48-hour wait (statistical significance guard)
- `weekly_subject_optimization(crm: CRMClient, openai: EmailGenerationClient) -> List[str]`
  - Called by weekly scheduler
  - Pulls last 4 weeks of campaign analytics from CRM
  - Sends top/bottom performers to OpenAI with prompt: "Based on these results, suggest 5 improved subject lines"
  - Returns list of optimized subject line suggestions for human review

---

### 1.4 `src/crm/hubspot_client.py`

**Purpose**: HubSpot implementation of `CRMClient` base class.

**Class: `HubSpotClient(CRMClient)`**
- Implements all 6 abstract methods from `src/crm/base.py`
- Uses `hubspot-api-client` library with API key from `settings.hubspot_api_key`
- Contact properties to map: `email`, `firstname`, `lifecycle_stage`, `hs_lead_status`, `last_modified_date`
- Segment filtering uses HubSpot contact list API or filter by property
- Campaign creation maps to HubSpot Marketing Email API
- Analytics pulled from HubSpot campaign performance endpoints

**Error handling**: Raise `CRMError` on 4xx/5xx responses; retry once on 429 (rate limit) with 1s delay.

---

### 1.5 `src/crm/convertkit_client.py`

**Purpose**: ConvertKit implementation of `CRMClient` base class.

**Class: `ConvertKitClient(CRMClient)`**
- Implements all 6 abstract methods from `src/crm/base.py`
- Uses ConvertKit v4 REST API with `settings.convertkit_api_key`
- Segment filtering maps to ConvertKit Tags and Segments
- Campaign creation maps to ConvertKit Broadcasts
- Analytics pulled from ConvertKit stats endpoints
- **Note**: API is read-heavy — batch subscriber fetches (up to 1000 per call)

---

### 1.6 `src/integrations/stripe_webhook.py`

**Purpose**: Receives Stripe events and triggers email automation.

**Class: `StripeWebhookHandler`**
- `handle_event(payload: bytes, signature: str) -> dict`
  - Validates signature using `stripe_webhook_secret` before processing
  - Raises `WebhookValidationError` on invalid signature
- Event handlers (each is idempotent — safe to replay):
  - `customer.subscription.created` → trigger `onboarding` sequence
  - `customer.subscription.updated` (tier upgrade) → trigger upsell confirmation email
  - `customer.subscription.deleted` → mark contact as `churned`, start reactivation timer
  - `invoice.payment_failed` → trigger payment recovery email sequence
- Deduplication: store event IDs in DB; skip if already processed within 24 hours

**Webhook server**: Lightweight FastAPI or Flask endpoint at `POST /webhooks/stripe`

---

### 1.7 `src/analytics/tracker.py`

**Purpose**: Records open, click, and conversion events per email.

**Class: `EmailTracker`**
- `record_open(email_id: str, contact_id: str, timestamp: datetime) -> None`
- `record_click(email_id: str, contact_id: str, link: str, timestamp: datetime) -> None`
- `record_conversion(email_id: str, contact_id: str, conversion_type: str, timestamp: datetime) -> None`
  - `conversion_type`: one of `"phoenix_signup"`, `"visionary_upgrade"`, `"infinity_upgrade"`, `"purchase"`
- All events stored in local SQLite DB (or external DB if `DATABASE_URL` is configured)

---

### 1.8 `src/analytics/reporter.py`

**Purpose**: Aggregates metrics and generates weekly performance reports.

**Class: `AnalyticsReporter`**
- `get_campaign_summary(campaign_id: str) -> EmailAnalytics`
  - Aggregates tracker data into `EmailAnalytics` Pydantic model (`src/models/email.py`)
- `weekly_report() -> dict`
  - Returns summary of all campaigns in last 7 days
  - Includes: top/bottom open rate, best/worst CTR, conversion rate by segment
  - Output used by `CampaignOptimizer.weekly_subject_optimization()`
- `flag_underperformers(threshold_open_rate: float = 0.15) -> List[str]`
  - Returns campaign IDs with open rate below threshold for human review

---

### 1.9 `src/prompts/` — Prompt Library

**`email_sequences.yaml`** structure:
```yaml
sequences:
  onboarding:
    total_emails: 7
    emails:
      - step: 1
        tone: "warm, welcoming"
        purpose: "Welcome + community intro"
        cta: "Explore Path of the Phoenix"
        key_messages: ["alignment", "renewal", "conscious evolution"]
      # ... steps 2-7
  upsell_phoenix_visionary:
    total_emails: 5
    emails:
      - step: 1
        tone: "aspirational, value-focused"
        purpose: "Highlight frequency healing and biometrics"
        cta: "Upgrade to Visionary"
  # cold_outbound (20-email full sequence from PDF)
  # reactivation
  # upsell_visionary_infinity
```

**`guardrails.yaml`** — extracted from OHM Brand Voice Guide:
```yaml
tone:
  allowed: ["modern", "aspirational", "non-dogmatic", "scientific", "mystical blend"]
  forbidden: ["clinical", "preachy", "religious", "guaranteed cure"]

hard_prohibitions:
  - "Do not claim OHM diagnoses or treats mental health conditions"
  - "Do not position OHM as a religion, church, or religious organization"
  - "Do not promise refunds or money-back guarantees"
  - "Do not claim OHM replaces licensed therapy or medical care"
  - "Do not make new medical claims beyond those on the OHM site"

safe_phrases:
  - "alignment, renewal, conscious evolution"
  - "a place for honest evolution"
  - "universal harmony"
  - "frequency-based EMF longevity therapy"
  - "digital-first spiritual platform"
  - "modern spiritual ecosystem"

membership_pricing:
  note: "Always pull live from CRM/backend — do not hardcode prices"
  tiers: ["Phoenix", "Visionary", "Infinity"]
```

---

## 2. Data Models to Add

### `src/models/campaign.py`
```python
class ABTestResult(BaseModel):
    test_id: str
    campaign_a_id: str
    campaign_b_id: str
    winner_id: Optional[str]   # Set after evaluation
    sample_size_a: int
    sample_size_b: int
    open_rate_a: float
    open_rate_b: float
    evaluated_at: Optional[datetime]
    is_statistically_significant: bool
```

### `src/models/analytics.py`
```python
class WeeklyReport(BaseModel):
    week_ending: datetime
    total_emails_sent: int
    avg_open_rate: float
    avg_ctr: float
    avg_conversion_rate: float
    top_campaign_id: str
    bottom_campaign_id: str
    subject_line_suggestions: List[str]
    underperforming_campaigns: List[str]
```

### `src/models/webhook.py`
```python
class StripeEvent(BaseModel):
    event_id: str
    event_type: str
    customer_id: str
    subscription_id: Optional[str]
    tier: Optional[str]         # "phoenix", "visionary", "infinity"
    received_at: datetime
    processed: bool = False
```

---

## 3. Configuration Updates

`src/config.py` needs two additions:
- `crm_provider` should not require validation at import time (wrap in lazy validation)
- Add `webhook_port: int = 8000` for the webhook server

---

## 4. Upsell Trigger Logic

Automation rules (implemented in `src/agent/email_generator.py` or a new `src/agent/automations.py`):

| Trigger | Sequence | Timing |
|---|---|---|
| `customer.subscription.created` (Phoenix) | `onboarding` | Immediately |
| Contact is `active_phoenix` for 30 days | `upsell_phoenix_visionary` | Day 30 |
| Contact is `active_visionary` for 30 days | `upsell_visionary_infinity` | Day 30 |
| `customer.subscription.deleted` | `reactivation` | 7 days after churn |
| `invoice.payment_failed` | payment recovery (2-email sequence) | Same day + Day 3 |

---

## 5. Brand Voice Compliance Rules (from OHM Docs)

The guardrail validator in `email_generator.py` must enforce:

**Always use:**
- "digital-first spiritual platform" — not "app" or "website"
- "universal harmony", "conscious evolution", "alignment and renewal"
- "frequency-based EMF longevity therapy" — not "healing device" or "medical device"
- "spiritual and reflective guide" — not "therapist" or "coach"

**Never use:**
- Diagnoses language ("treat depression", "cure anxiety")
- Religious org framing ("church", "sect", "temple membership")
- Guarantee language ("risk-free", "money-back")
- Hard-coded pricing (always reference live source)
- New scientific claims beyond what is on the OHM site

---

## 6. File Creation Plan

Files to create (all new, building on existing skeleton):

| File | Depends On |
|---|---|
| `src/prompts/guardrails.yaml` | OHM brand doc |
| `src/prompts/email_sequences.yaml` | 20-email PDF + brand doc |
| `src/agent/email_generator.py` | `openai_client.py`, `guardrails.yaml` |
| `src/agent/segmentation.py` | `crm/base.py` |
| `src/agent/optimizer.py` | `models/email.py`, `crm/base.py` |
| `src/crm/hubspot_client.py` | `crm/base.py` |
| `src/crm/convertkit_client.py` | `crm/base.py` |
| `src/integrations/stripe_webhook.py` | `models/webhook.py`, `config.py` |
| `src/analytics/tracker.py` | `models/email.py`, SQLAlchemy |
| `src/analytics/reporter.py` | `tracker.py`, `models/analytics.py` |
| `src/models/campaign.py` | Pydantic |
| `src/models/analytics.py` | Pydantic |
| `src/models/webhook.py` | Pydantic |
| `src/main.py` (update) | All modules |

---

## 7. Verification Plan

1. **Unit tests** — `pytest tests/` after each module is written
   - `tests/agent/test_email_generator.py` — mock OpenAI, test guardrail violations
   - `tests/agent/test_segmentation.py` — test segment classification logic
   - `tests/crm/test_hubspot_client.py` — mock HubSpot API responses
   - `tests/integrations/test_stripe_webhook.py` — mock Stripe events, check idempotency

2. **Integration smoke test**
   ```bash
   python -m src.main  # Should start without errors with valid .env
   ```

3. **Guardrail test**
   - Pass an email containing "cure depression" → should raise `GuardrailViolationError`
   - Pass a valid email → should return `True`

4. **Segmentation test**
   - Mock CRM contacts with different lifecycle stages → verify correct segments returned

5. **Weekly optimizer test**
   - Seed analytics DB with sample data → call `weekly_report()` → verify report fields populated
