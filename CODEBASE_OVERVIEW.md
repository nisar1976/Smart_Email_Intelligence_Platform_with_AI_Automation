# Email Intelligence Agent - Codebase Overview

## Project Structure

```
src/
├── agent/                      # Email generation & optimization
│   ├── email_generator.py      # Email sequence generation with guardrails
│   ├── segmentation.py         # Behavioral audience segmentation
│   └── optimizer.py            # A/B testing & weekly optimization
├── crm/                        # CRM integrations (abstraction pattern)
│   ├── base.py                 # Abstract CRMClient base class
│   ├── hubspot_client.py       # HubSpot API implementation
│   └── convertkit_client.py    # ConvertKit API implementation
├── integrations/               # External service integrations
│   ├── openai_client.py        # OpenAI API wrapper
│   └── stripe_webhook.py       # Stripe event handling
├── analytics/                  # Performance tracking & reporting
│   ├── tracker.py              # Open/click/conversion events
│   └── reporter.py             # Weekly reports & aggregations
├── models/                     # Pydantic data models
│   ├── email.py                # Email, EmailCampaign, EmailAnalytics
│   ├── campaign.py             # ABTestResult
│   ├── analytics.py            # WeeklyReport
│   └── webhook.py              # StripeEvent
├── prompts/                    # AI prompt templates & guardrails
│   ├── email_sequences.yaml    # 5 campaign types (20-email cold outbound)
│   └── guardrails.yaml         # OHM brand voice rules
├── config.py                   # Environment configuration
└── main.py                     # Agent orchestrator & entry point
```

---

## Core Architecture

### 1. **Agent Orchestrator** (`src/main.py`)
**Class: `EmailIntelligenceAgent`**

Central orchestrator that initializes and manages all subsystems:

```
EmailIntelligenceAgent
├── CRM Client (HubSpot or ConvertKit)
├── EmailGenerator
│   ├── OpenAI Client
│   ├── Guardrails (YAML-loaded)
│   └── Email Sequences (YAML-loaded)
├── AudienceSegmentor
├── CampaignOptimizer
├── EmailTracker
├── AnalyticsReporter
└── StripeWebhookHandler
```

**Key Methods:**
- `_init_crm()` - Factory for HubSpot/ConvertKit
- `run_segmentation()` - Classify all contacts into 7 behavioral segments
- `generate_campaign_sequence()` - Orchestrate email generation
- `get_weekly_report()` - Aggregate performance metrics
- `start_webhook_server()` - FastAPI server for Stripe events

---

### 2. **Email Generation Pipeline** (`src/agent/email_generator.py`)

**3-Step Process:**

```
Campaign Request
    ↓
1. Load Templates (YAML)
    ↓
2. Call OpenAI with Context
    ↓
3. Validate Against Guardrails (2nd OpenAI Call)
    ↓
Email Objects (with subject, body, segment, step)
```

**GuardrailViolationError Triggers:**
- Medical claims ("cure", "treat", "clinical")
- Religious framing ("church", "temple", "sect")
- Guarantee language ("risk-free", "money-back")
- Replaces professional care ("instead of therapy")

**Campaign Types:**
| Type | Steps | Purpose |
|------|-------|---------|
| `onboarding` | 7 | Welcome new Phoenix members |
| `upsell_phoenix_visionary` | 5 | Upgrade path (30+ day trigger) |
| `upsell_visionary_infinity` | 5 | Premium upgrade path |
| `reactivation` | 6 | Win-back for churned members |
| `cold_outbound` | 20 | Full acquisition sequence |

---

### 3. **Audience Segmentation** (`src/agent/segmentation.py`)

**7 Behavioral Segments:**

```
Contact Classification Logic:
│
├─ No subscription? → cold_prospect
├─ Phoenix < 7 days? → new_phoenix
├─ Phoenix + active (14d)? → active_phoenix
├─ Phoenix + 30d + clicked upsell? → upsell_candidate_visionary
├─ Visionary + 30d + clicked upsell? → upsell_candidate_infinity
├─ No login 60+ days? → churned
└─ Churned 90+ days? → reactivation
```

**Input:** Contact dict with:
- `lifecycle_stage`, `subscription_tier`, `last_activity_date`
- `subscription_created_date`, `subscription_cancelled_date`
- `clicked_upsell_cta` (boolean)

**Output:** Segment name for routing to appropriate email sequence

---

### 4. **CRM Abstraction Pattern** (`src/crm/base.py`)

**Abstract Base Class:**

```python
CRMClient (ABC)
├── get_contacts(segment, limit) → List[Dict]
├── create_campaign(name, emails) → campaign_id
├── send_campaign(campaign_id) → deployment_dict
├── get_analytics(campaign_id) → metrics_dict
├── segment_contacts(criteria) → List[contact_ids]
└── update_contact(contact_id, data) → bool
```

**Implementations:**

1. **HubSpotClient** (`src/crm/hubspot_client.py`)
   - Uses `hubspot-api-client` library
   - API-key auth with Bearer token
   - Maps HubSpot properties (lifecyclestage, hs_lead_status, etc.)
   - Handles pagination & rate limiting (429 with 1s retry)

2. **ConvertKitClient** (`src/crm/convertkit_client.py`)
   - ConvertKit v3 REST API
   - Tag-based segmentation
   - Broadcasts for campaigns
   - Batch subscriber fetch (1000/call)

**Error Handling:** `CRMError` on API failures, with retry logic for rate limits

---

### 5. **A/B Testing & Optimization** (`src/agent/optimizer.py`)

**A/B Test Workflow:**

```
Original Campaign (N recipients)
    ↓
create_ab_test(campaign, variant_b_subject)
    ↓
Split 50/50
    ├─ Variant A (N/2 recipients, original subject)
    └─ Variant B (N/2 recipients, alternative subject)
    ↓
Send both (48hr+ wait required)
    ↓
evaluate_ab_test()
    ├─ Compare open rates
    ├─ Check significance (>5% difference)
    └─ Return winner_id
```

**Weekly Optimization:**
1. Pull last 4 weeks of analytics
2. Identify top 3 & bottom 3 performers
3. Send to OpenAI: "Suggest 5 improved subject lines"
4. Return suggestions for human review

**Guardrails:**
- Min 100 recipients/variant for statistical validity
- 48-hour minimum wait before evaluation
- >5% difference required for significance

---

### 6. **Stripe Webhook Handler** (`src/integrations/stripe_webhook.py`)

**Event Flow:**

```
Stripe Event (POST /webhooks/stripe)
    ↓
Validate Signature (HMAC-SHA256)
    ↓
Parse Event (customer_id, subscription_id, tier)
    ↓
Deduplicate (event_id in DB, skip if processed)
    ↓
Route to Handler:
├─ customer.subscription.created → trigger onboarding
├─ customer.subscription.updated → trigger upgrade_confirmation
├─ customer.subscription.deleted → mark churned + schedule reactivation (7d)
├─ invoice.payment_failed → trigger payment_recovery (2-email)
└─ invoice.payment_succeeded → clear payment failure flag
```

**Idempotency:** Events stored in SQLite with `processed` flag; safe to replay

**Tier Detection:** Extract from Stripe subscription metadata/product_id

---

### 7. **Analytics Pipeline** (`src/analytics/tracker.py` + `reporter.py`)

**Event Tracking (SQLite):**

```
Three Tables:
├─ email_opens (email_id, contact_id, timestamp)
├─ email_clicks (email_id, contact_id, link, timestamp)
└─ email_conversions (email_id, contact_id, type, timestamp)
                                              ├─ phoenix_signup
                                              ├─ visionary_upgrade
                                              ├─ infinity_upgrade
                                              └─ purchase
```

**Reporting:**

```
get_campaign_summary(campaign_id)
    ↓
Aggregate all events for campaign
    ↓
Calculate rates: open_rate, CTR, conversion_rate
    ↓
Return EmailAnalytics object

weekly_report(analytics_data)
    ↓
├─ Total emails sent
├─ Avg open rate, CTR, conversion
├─ Top/bottom performers
├─ Subject line suggestions (from optimizer)
└─ Underperformers (< 80% of avg)
```

---

## Data Models

### Email & Campaign (`src/models/email.py`)
```python
Email
├── subject, body, recipient_email, recipient_id
├── campaign_id, sequence_step, segment
└── sent_at, opened_at, clicked_at, converted_at

EmailCampaign
├── id, name, description
├── emails: List[Email]
├── target_segment, upsell_type
├── created_at, sent_at, is_abtest

EmailAnalytics
├── campaign_id, total_sent, total_opened, total_clicked
├── open_rate, click_through_rate, conversion_rate
└── last_updated
```

### A/B Testing (`src/models/campaign.py`)
```python
ABTestResult
├── test_id, campaign_a_id, campaign_b_id
├── winner_id, is_statistically_significant
├── sample_size_a, sample_size_b
├── open_rate_a, open_rate_b
└── evaluated_at
```

### Analytics (`src/models/analytics.py`)
```python
WeeklyReport
├── week_ending, total_emails_sent
├── avg_open_rate, avg_ctr, avg_conversion_rate
├── top_campaign_id, bottom_campaign_id
├── subject_line_suggestions
└── underperforming_campaigns
```

### Webhooks (`src/models/webhook.py`)
```python
StripeEvent
├── event_id, event_type
├── customer_id, subscription_id, tier
├── received_at, processed
```

---

## Configuration (`src/config.py`)

**Pydantic Settings with environment variables:**

```python
Settings
├── OpenAI
│   ├── openai_api_key (required)
│   └── openai_model (default: "gpt-4")
├── CRM
│   ├── crm_provider: "hubspot" | "convertkit"
│   ├── hubspot_api_key (if hubspot)
│   └── convertkit_api_key (if convertkit)
├── Stripe
│   ├── stripe_api_key (optional)
│   └── stripe_webhook_secret (required if webhook enabled)
├── Email
│   ├── sender_email, sender_name
├── Server
│   ├── webhook_port (default: 8000)
├── Database
│   └── database_url (default: "sqlite:///./email_agent.db")
└── Logging
    ├── environment: "development" | "staging" | "production"
    └── log_level (default: "INFO")
```

**All credentials loaded from `.env` file (never committed)**

---

## Prompt Library

### `src/prompts/guardrails.yaml`

**Brand Voice Rules:**

```yaml
tone:
  allowed: ["modern", "aspirational", "non-dogmatic", "scientific", "mystical blend"]
  forbidden: ["clinical", "preachy", "religious", "guaranteed cure"]

hard_prohibitions: [
  "Do not claim OHM diagnoses or treats mental health",
  "Do not position OHM as a religion",
  "Do not promise refunds/guarantees",
  "Do not claim OHM replaces licensed therapy",
  "Do not make claims beyond OHM site"
]

safe_phrases:
  - "alignment, renewal, conscious evolution"
  - "frequency-based EMF longevity therapy"
  - "digital-first spiritual platform"

terminology:
  correct_terms:
    platform: "digital-first spiritual platform" (not "app")
    healing: "frequency-based EMF longevity therapy" (not "medical device")
    guide: "spiritual and reflective guide" (not "therapist")
```

### `src/prompts/email_sequences.yaml`

**5 Campaign Definitions:**

Each campaign has multiple email steps with:
- `tone` - email voice
- `purpose` - what the email does
- `cta` - call-to-action text
- `key_messages` - brand values to emphasize
- `length` - "short", "medium", or "long"

**Example (cold_outbound):**
```yaml
cold_outbound:
  total_emails: 20
  emails:
    - step: 1
      tone: "curious, non-pushy"
      purpose: "Introduction - what is OHM?"
      cta: "Learn more"
      key_messages: ["digital-first spiritual platform", "modern approach"]
      length: "short"
    - step: 2
      tone: "relatable, aspirational"
      purpose: "The problem most people face"
      ...
    # ... steps 3-20
```

---

## Data Flow

### **Email Generation Flow:**

```
Contact → Segmentation
    ↓
Segment Name (e.g., "active_phoenix")
    ↓
Select Campaign Type (e.g., "upsell_phoenix_visionary")
    ↓
Load YAML Templates + Guardrails
    ↓
For each email step:
├─ Build context dict with segment, tone, CTA, key_messages
├─ Call OpenAI (generate_email) → raw content
├─ Call OpenAI (validate_against_guardrails) → pass/fail
├─ Raise GuardrailViolationError if failed
└─ Create Email object
    ↓
Return List[Email] (full sequence)
```

### **Campaign Deployment Flow:**

```
Email List → CRM create_campaign()
    ↓
Campaign created in HubSpot/ConvertKit
    ↓
CRM send_campaign()
    ↓
Tracking pixels embedded in emails
    ↓
Stripe events trigger automations
    ↓
User interactions recorded in tracker DB
```

### **Analytics Flow:**

```
Email Open Event
    ↓
EmailTracker.record_open()
    ↓
Insert into email_opens table
    ↓
Pixel fire (from CRM or email client)
    ↓
AnalyticsReporter.get_campaign_summary()
    ↓
Aggregate: total_opened / total_sent = open_rate
    ↓
Weekly summary via weekly_report()
```

---

## Integration Points

### **External APIs:**

1. **OpenAI API**
   - Email generation (1 call per email)
   - Subject line optimization (1 call per week)
   - Guardrail validation (1 call per email)

2. **HubSpot API**
   - Get/update contacts
   - Create/send campaigns
   - Fetch campaign analytics
   - Manage lifecycle stages

3. **ConvertKit API**
   - Fetch subscribers
   - Create broadcasts
   - Manage tags/segments
   - Get subscriber stats

4. **Stripe API**
   - Webhook events (subscription lifecycle, payments)
   - Event signature validation

5. **Email Service**
   - Pixel tracking (opens, clicks)
   - Link click tracking
   - Conversion events

### **Webhook Events:**

```
Stripe → POST /webhooks/stripe
    ↓
StripeWebhookHandler.handle_event()
    ↓
Registered handlers triggered
    ↓
Automation workflows initiated
```

---

## Error Handling

**Custom Exceptions:**

| Exception | Raised By | Handled | Recovery |
|-----------|-----------|---------|----------|
| `GuardrailViolationError` | EmailGenerator | Caller | Manual review required |
| `CRMError` | CRM clients | Caller | Retry with exponential backoff |
| `WebhookValidationError` | StripeWebhookHandler | Caller | Log + return 400 |

**Rate Limiting:**
- CRM: 429 status → retry once after 1 second
- Webhook: Signature timestamp validation (within 5 minutes)

**Deduplication:**
- Stripe events: Store in DB, check `processed` flag
- Email operations: Idempotent at each step

---

## Testing Structure

```
tests/
├── agent/
│   └── test_email_generator.py
│   └── test_segmentation.py
├── crm/
│   └── test_hubspot_client.py
├── integrations/
│   └── test_stripe_webhook.py
```

**Mock Requirements:**
- OpenAI API responses
- HubSpot/ConvertKit API responses
- Stripe webhook events
- Database state

---

## Dependencies

**Core:**
- `pydantic` - data models
- `python-dotenv` - environment loading
- `openai` - GPT-4 API
- `requests` - HTTP requests
- `PyYAML` - YAML parsing
- `sqlite3` - default DB (built-in)

**Optional:**
- `fastapi` + `uvicorn` - webhook server
- `hubspot-api-client` - HubSpot integration
- `stripe` - Stripe SDK
- `pytest` - testing

---

## Deployment Checklist

- [ ] `.env` configured with all API keys
- [ ] Database initialized (SQLite or external)
- [ ] OpenAI API key validated
- [ ] CRM provider credentials tested
- [ ] Stripe webhook secret configured
- [ ] Webhook server listening on `webhook_port`
- [ ] Brand guardrails reviewed by OHM team
- [ ] Email sequence templates tested
- [ ] Segmentation logic verified with sample contacts
- [ ] A/B test minimum sample size rules documented
- [ ] Weekly optimization scheduler configured
- [ ] Logging centralized and monitored

---

## Future Enhancements

- [ ] Database migrations (Alembic)
- [ ] Event queue (Redis/Celery) for async processing
- [ ] ML-based send time optimization
- [ ] Dynamic content personalization
- [ ] Predictive churn scoring
- [ ] Multi-channel support (SMS, push)
- [ ] Advanced analytics dashboards
- [ ] Webhook retry mechanism with exponential backoff
