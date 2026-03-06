# Email Intelligence Agent - Architecture Diagrams

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EMAIL INTELLIGENCE AGENT                               │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    EmailIntelligenceAgent (Orchestrator)               │   │
│  │                                                                        │   │
│  │  Initializes & manages all subsystems                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CRM Client │  │ EmailGenerator│  │  Segmentor   │  │  Optimizer   │      │
│  │ (HubSpot or  │  │  (OpenAI +   │  │  (7 segments)│  │  (A/B Test)  │      │
│  │ ConvertKit)  │  │  Guardrails) │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                        │
│  │   Tracker    │  │  Reporter    │  │   Webhook    │                        │
│  │ (Open/Click/ │  │ (Analytics & │  │  Handler     │                        │
│  │  Conversion) │  │  Reports)    │  │ (Stripe)     │                        │
│  └──────────────┘  └──────────────┘  └──────────────┘                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Email Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EMAIL GENERATION FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Request
┌─────────────────┐
│ Contact + Segment│  (e.g., "active_phoenix")
│ Campaign Type   │  (e.g., "upsell_phoenix_visionary")
│ Recipients: 100 │
└────────┬────────┘
         │
         ▼

Step 2: Load Configuration
    ┌──────────────────────────────────────────┐
    │ email_sequences.yaml                     │
    │ ├─ onboarding (7 emails)                 │
    │ ├─ upsell_phoenix_visionary (5 emails)   │
    │ ├─ upsell_visionary_infinity (5 emails)  │
    │ ├─ reactivation (6 emails)               │
    │ └─ cold_outbound (20 emails)             │
    └────────┬─────────────────────────────────┘
             │
    ┌────────▼───────────────────┐
    │ guardrails.yaml            │
    │ ├─ tone (allowed/forbidden)│
    │ ├─ hard_prohibitions       │
    │ ├─ safe_phrases            │
    │ └─ terminology             │
    └────────┬───────────────────┘
             │
         ▼

Step 3: For Each Email Step (1 → N)
    ┌─────────────────────────────────────────┐
    │ Build Email Context:                    │
    │ - tone, purpose, CTA                    │
    │ - key_messages, length                  │
    │ - guardrails text                       │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ Call OpenAI #1                          │
    │ generate_email()                        │
    │ → Raw email content (body + subject)    │
    └────────┬────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ Call OpenAI #2                          │
    │ validate_against_guardrails()           │
    │ → PASS or FAIL                          │
    └────────┬────────────────────────────────┘
             │
        ┌────┴────┐
        │          │
        ▼          ▼
      FAIL        PASS
       │            │
       │            ▼
       │         ┌─────────────────┐
       │         │ Create Email Obj│
       │         │ - subject       │
       │         │ - body          │
       │         │ - segment       │
       │         │ - step (1 of N) │
       │         └────────┬────────┘
       │                  │
       │                  ▼
       │         ┌─────────────────┐
       │         │ Add to List     │
       │         │ (repeat for each│
       │         │  recipient)     │
       │         └────────┬────────┘
       │                  │
       │                  │ (100 recipients)
       │                  ▼
       │         ┌─────────────────┐
       │         │ List[Email]     │
       │         │ 100 emails      │
       │         │ per step        │
       │         └─────────────────┘
       │
       ▼
    ┌──────────────────┐
    │GuardrailViolation│
    │Error Raised      │
    │                  │
    │⚠️ Medical claims │
    │⚠️ Religion frame │
    │⚠️ Guarantees     │
    │⚠️ Therapy repla. │
    └──────────────────┘
         ▲
         │
         └─ Human Review Required

Result: List[Email] (sequence ready to deploy)
```

---

## 3. Segmentation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUDIENCE SEGMENTATION FLOW                       │
└─────────────────────────────────────────────────────────────────────┘

Input: All Contacts from CRM
       ├─ id, email, firstname, lastname
       ├─ lifecycle_stage, subscription_tier
       ├─ last_activity_date
       ├─ subscription_created_date
       ├─ subscription_cancelled_date
       └─ clicked_upsell_cta (boolean)

       │
       ▼

Decision Tree (per contact):
┌───────────────────────┐
│ No subscription?      │─────────────────► cold_prospect
└───────────┬───────────┘
            │ Yes, has subscription
            ▼
┌───────────────────────┐
│ Tier = Phoenix        │
│ Age < 7 days?         │─────────────────► new_phoenix
└───────────┬───────────┘
            │ No or other tier
            ▼
┌───────────────────────┐
│ Tier = Phoenix        │
│ Last active < 14d?    │─────────────────► active_phoenix
└───────────┬───────────┘
            │ No
            ▼
┌───────────────────────┐
│ Tier = Phoenix        │
│ Age >= 30d AND        │
│ Clicked upsell?       │─────────────────► upsell_candidate_visionary
└───────────┬───────────┘
            │ No
            ▼
┌───────────────────────┐
│ Tier = Visionary      │
│ Age >= 30d AND        │
│ Clicked upsell?       │─────────────────► upsell_candidate_infinity
└───────────┬───────────┘
            │ No
            ▼
┌───────────────────────┐
│ No login >= 60d?      │─────────────────► churned
└───────────┬───────────┘
            │ No
            ▼
┌───────────────────────┐
│ Churned > 90 days?    │─────────────────► reactivation
│ Previously active?    │
└───────────┬───────────┘
            │ No
            ▼
           cold_prospect (fallback)

Output:
┌──────────────────────────────────────────┐
│ Segment Dict:                            │
│ {                                        │
│   "cold_prospect": [id1, id2, ...],      │
│   "new_phoenix": [id3, id4, ...],        │
│   "active_phoenix": [id5, ...],          │
│   "upsell_candidate_visionary": [...],   │
│   "upsell_candidate_infinity": [...],    │
│   "churned": [...],                      │
│   "reactivation": [...]                  │
│ }                                        │
└──────────────────────────────────────────┘
```

---

## 4. Campaign Deployment & Tracking

```
┌─────────────────────────────────────────────────────────────────────┐
│                 CAMPAIGN DEPLOYMENT & TRACKING FLOW                 │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Generate Sequence
┌──────────────────┐
│ EmailGenerator   │
│ generates List   │
│ [Email] objects  │
└────────┬─────────┘
         │

Step 2: Create Campaign in CRM
         │
         ▼
    ┌─────────────────────────────────────┐
    │ CRM.create_campaign()                │
    │ ├─ HubSpot: Marketing Email API      │
    │ └─ ConvertKit: Broadcasts API        │
    └────────┬────────────────────────────┘
             │
             ▼ campaign_id

Step 3: Deploy Campaign
    ┌────────────────────────────┐
    │ CRM.send_campaign()         │
    │                            │
    │ Emails sent to:            │
    │ - recipient_1@email.com    │
    │ - recipient_2@email.com    │
    │ - ... 100 total            │
    └────────┬───────────────────┘
             │
             ▼

Step 4: Embed Tracking
    ┌────────────────────────────────────┐
    │ Email Content:                     │
    │                                   │
    │ Subject: [subject line]            │
    │ Body: [content]                    │
    │                                   │
    │ + Tracking pixels:                 │
    │ - <img src="track/open/...">       │
    │ - <a href="click-wrapper/...">CTA  │
    │                                   │
    │ Recipient gets personalized        │
    │ tracking URL per click             │
    └────────┬───────────────────────────┘
             │
             ▼

Step 5: User Interactions
    ┌─────────────────────────────────┐
    │ 1. User opens email              │
    │    → Pixel fires                  │
    │    → EmailTracker.record_open()  │
    │                                  │
    │ 2. User clicks link              │
    │    → Click wrapper triggered     │
    │    → EmailTracker.record_click() │
    │                                  │
    │ 3. User converts (purchase)      │
    │    → Webhook from CRM or Stripe  │
    │    → EmailTracker.record_conv()  │
    └────────┬────────────────────────┘
             │
             ▼

Step 6: Analytics Collection
    ┌──────────────────────────────────┐
    │ SQLite Tables:                   │
    │                                  │
    │ email_opens                      │
    │ ├─ email_id, contact_id, time    │
    │                                  │
    │ email_clicks                     │
    │ ├─ email_id, contact_id, link    │
    │                                  │
    │ email_conversions                │
    │ ├─ email_id, contact_id, type    │
    │   (phoenix_signup, upgrade, etc.)│
    └────────┬───────────────────────┘
             │
             ▼

Step 7: Generate Reports
    ┌──────────────────────────────────┐
    │ AnalyticsReporter                │
    │                                  │
    │ For each campaign:               │
    │ - total_sent: 100                │
    │ - total_opened: 25               │
    │ - total_clicked: 8               │
    │ - total_converted: 2             │
    │                                  │
    │ Calculated rates:                │
    │ - open_rate: 25%                 │
    │ - CTR: 8%                        │
    │ - conversion_rate: 2%            │
    └────────┬───────────────────────┘
             │
             ▼
    ┌──────────────────────────────────┐
    │ Weekly Report:                   │
    │ - avg_open_rate across campaigns │
    │ - top/bottom performers          │
    │ - underperformers list           │
    │ - subject optimization suggestions│
    └──────────────────────────────────┘
```

---

## 5. Stripe Webhook Automation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              STRIPE WEBHOOK AUTOMATION TRIGGER FLOW             │
└─────────────────────────────────────────────────────────────────┘

Stripe Event Occurs
        │
        ▼
POST /webhooks/stripe
        │
        ├─ Payload (JSON)
        └─ Signature Header (HMAC-SHA256)
        │
        ▼

Step 1: Validate Signature
    ┌──────────────────────────────┐
    │ StripeWebhookHandler         │
    │ .handle_event()              │
    │                              │
    │ Compute expected HMAC        │
    │ Compare with header          │
    │                              │
    │ ✓ PASS → continue            │
    │ ✗ FAIL → WebhookValidation   │
    │          Error               │
    └────────┬─────────────────────┘
             │
             ▼

Step 2: Parse Event
    Extract:
    - event_id (for deduplication)
    - event_type (subscription.created, etc.)
    - customer_id
    - subscription_id
    - tier (phoenix, visionary, infinity)
        │
        ▼

Step 3: Check Deduplication
    ┌────────────────────────────┐
    │ Query stripe_events table   │
    │ WHERE event_id = ?          │
    │                            │
    │ ✓ Found & processed=1       │
    │   → Skip (already handled)  │
    │                            │
    │ ✗ Not found                 │
    │   → Process (continue)      │
    └────────┬───────────────────┘
             │
             ▼

Step 4: Route to Handler
    ┌────────────────────────────────────────────────┐
    │ Event Type Decision Tree:                       │
    │                                                │
    │ customer.subscription.created                  │
    │ └─► _handle_subscription_created()             │
    │     └─► Trigger "onboarding" sequence          │
    │         (7 emails for new Phoenix members)     │
    │                                                │
    │ customer.subscription.updated                  │
    │ └─► _handle_subscription_updated()             │
    │     ├─ If tier upgrade: upgrade_confirmation  │
    │     └─ Call registered handlers                │
    │                                                │
    │ customer.subscription.deleted                  │
    │ └─► _handle_subscription_deleted()             │
    │     ├─ Mark contact as churned                 │
    │     └─ Schedule reactivation in 7 days         │
    │         (6 emails to win back member)          │
    │                                                │
    │ invoice.payment_failed                         │
    │ └─► _handle_payment_failed()                   │
    │     └─ Trigger payment recovery sequence       │
    │         (2 emails: immediate + day 3)          │
    │                                                │
    │ invoice.payment_succeeded                      │
    │ └─► _handle_payment_succeeded()                │
    │     └─ Clear payment failure flag              │
    └────────┬───────────────────────────────────────┘
             │
             ▼

Step 5: Trigger Email Automation
    ┌─────────────────────────────────┐
    │ EmailGenerator                  │
    │ .generate_sequence()            │
    │                                 │
    │ Campaign Type:                  │
    │ - onboarding                    │
    │ - upgrade_confirmation          │
    │ - reactivation                  │
    │ - payment_recovery              │
    │                                 │
    │ Segment: auto-determined from   │
    │ contact data                    │
    └────────┬────────────────────────┘
             │
             ▼

Step 6: Deploy via CRM
    ┌──────────────────────┐
    │ CRM.create_campaign()│
    │ CRM.send_campaign()  │
    └────────┬─────────────┘
             │
             ▼

Step 7: Mark as Processed
    ┌────────────────────────────────┐
    │ INSERT into stripe_events       │
    │ (event_id, event_type, cust_id,│
    │  subscription_id, processed=1, │
    │  processed_at=now)              │
    │                                 │
    │ Prevents duplicate processing   │
    │ (safe to replay)                │
    └────────────────────────────────┘
```

---

## 6. A/B Test Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      A/B TEST WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

Start
  │
  ├─ Original Campaign
  │  ├─ 200 recipients
  │  ├─ Subject: "Unlock Your Potential"
  │  └─ Campaign ID: camp_123
  │
  ▼

Step 1: Create A/B Test
┌──────────────────────────────────────┐
│ CampaignOptimizer                    │
│ .create_ab_test(campaign, alt_subject)
│                                      │
│ alt_subject = "Level Up Your Journey"│
└────────┬─────────────────────────────┘
         │
         ▼

Step 2: Split Recipients 50/50
┌──────────────────────────────────┐
│                                  │
│  Variant A         Variant B      │
│  ├─ 100 recipients │100 recipients│
│  ├─ Original subject Original subject
│  ├─ camp_123_var_a │camp_123_var_b│
│  │                 │              │
│  └─────────────────┴──────────────┘
│
│  Constraints:
│  - Min 100 recipients/variant
│  - Must wait ≥ 48 hours before eval
│
└────────┬──────────────────────────┘
         │
         ▼

Step 3: Send Both Variants
┌─────────────────────────┐
│ CRM.send_campaign(var_a)│
│ CRM.send_campaign(var_b)│
└────────┬────────────────┘
         │
         │ 48+ hours pass
         │
         ▼

Step 4: Collect Metrics
┌─────────────────────────────────┐
│ AnalyticsReporter               │
│                                 │
│ Variant A:                      │
│ - Sent: 100                     │
│ - Opened: 20                    │
│ - Open rate: 20%                │
│                                 │
│ Variant B:                      │
│ - Sent: 100                     │
│ - Opened: 28                    │
│ - Open rate: 28%                │
│                                 │
│ Difference: 8%                  │
└────────┬────────────────────────┘
         │
         ▼

Step 5: Evaluate Statistical Significance
┌──────────────────────────────────┐
│ CampaignOptimizer                │
│ .evaluate_ab_test()              │
│                                  │
│ Threshold: >5% difference         │
│                                  │
│ 28% vs 20% = 8% difference        │
│ → SIGNIFICANT ✓                  │
│                                  │
│ Winner: Variant B                │
│ (Higher open rate)               │
└────────┬───────────────────────┘
         │
         ▼

Step 6: Document Results
┌──────────────────────────────────┐
│ ABTestResult                     │
│ {                                │
│   test_id: "test_abc123",        │
│   campaign_a_id: "camp_123_var_a",
│   campaign_b_id: "camp_123_var_b",
│   winner_id: "camp_123_var_b",   │
│   open_rate_a: 0.20,             │
│   open_rate_b: 0.28,             │
│   is_statistically_significant: true,
│   evaluated_at: 2026-03-05       │
│ }                                │
└────────┬───────────────────────┘
         │
         ▼

Step 7: Use Winner for Future Campaigns
┌──────────────────────────────────┐
│ Apply learning:                  │
│ "Level Up Your Journey" performs │
│ better for this segment           │
│                                  │
│ Use in next campaign to this      │
│ audience segment                 │
└──────────────────────────────────┘
```

---

## 7. Weekly Optimization Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│               WEEKLY OPTIMIZATION CYCLE                         │
└─────────────────────────────────────────────────────────────────┘

Sunday 11:59 PM (Weekly Scheduler Triggers)
        │
        ▼

Step 1: Collect Last 7 Days Analytics
┌──────────────────────────────────┐
│ AnalyticsReporter                │
│ .weekly_report()                 │
│                                  │
│ Aggregate all campaigns from:    │
│ - Last 7 days                    │
│                                  │
│ Calculate:                       │
│ - total_emails_sent: 50,000      │
│ - avg_open_rate: 22.5%           │
│ - avg_ctr: 4.2%                  │
│ - avg_conversion: 0.8%           │
└────────┬───────────────────────┘
         │
         ▼

Step 2: Identify Top & Bottom Performers
┌──────────────────────────────────┐
│ Sort by open_rate                │
│                                  │
│ Top 3:                           │
│ 1. "Your Evolution Awaits" - 35% │
│ 2. "Step Into Your Power" - 32%  │
│ 3. "Unlock Alignment" - 29%      │
│                                  │
│ Bottom 3:                        │
│ 1. "Check This Out" - 12%        │
│ 2. "New Update" - 14%            │
│ 3. "Important Message" - 15%     │
└────────┬───────────────────────┘
         │
         ▼

Step 3: Build Optimization Prompt
┌─────────────────────────────────────────┐
│ "Based on these email performance      │
│  metrics:                               │
│                                         │
│  TOP PERFORMERS:                        │
│  - "Your Evolution Awaits" (35% open)  │
│  - "Step Into Your Power" (32% open)   │
│  - "Unlock Alignment" (29% open)       │
│                                         │
│  BOTTOM PERFORMERS:                     │
│  - "Check This Out" (12% open)         │
│  - "New Update" (14% open)             │
│  - "Important Message" (15% open)      │
│                                         │
│  Generate 5 improved subject lines     │
│  combining best practices from top     │
│  performers while maintaining OHM      │
│  brand voice."                          │
└────────┬────────────────────────────────┘
         │
         ▼

Step 4: Call OpenAI for Suggestions
┌──────────────────────────────────┐
│ EmailGenerationClient            │
│ .optimize_subject_line()         │
│                                  │
│ Model: GPT-4                     │
│ Temperature: 0.7                 │
└────────┬───────────────────────┘
         │
         ▼

Step 5: Generate Suggestions
┌─────────────────────────────────────┐
│ 5 Optimized Subject Lines:          │
│                                     │
│ 1. "Your Conscious Evolution Starts │
│    Now"                             │
│                                     │
│ 2. "Step Into Universal Harmony"    │
│                                     │
│ 3. "Align Your Path to Renewal"    │
│                                     │
│ 4. "Unlock Your Potential Within"   │
│                                     │
│ 5. "Your Journey to Evolution       │
│    Begins Today"                    │
│                                     │
│ (All comply with guardrails ✓)      │
└────────┬────────────────────────────┘
         │
         ▼

Step 6: Generate Weekly Report
┌───────────────────────────────────┐
│ WeeklyReport                      │
│ {                                 │
│   week_ending: 2026-03-08,        │
│   total_emails_sent: 50000,       │
│   avg_open_rate: 0.225,           │
│   avg_ctr: 0.042,                 │
│   avg_conversion_rate: 0.008,     │
│   top_campaign_id: "camp_456",    │
│   bottom_campaign_id: "camp_789", │
│   subject_line_suggestions: [...],│
│   underperforming_campaigns: [...] │
│ }                                 │
└────────┬────────────────────────┘
         │
         ▼

Step 7: Human Review & Implementation
┌──────────────────────────────────────┐
│ OHM Marketing Team:                  │
│                                      │
│ 1. Review suggestions                │
│ 2. A/B test top 2 suggestions        │
│ 3. Apply winner to underperformers   │
│ 4. Adjust timing/frequency based on  │
│    conversion data                   │
│                                      │
│ Next week: Repeat cycle              │
└──────────────────────────────────────┘
```

---

## 8. Data Model Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA MODEL RELATIONSHIPS                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐
│ Email                        │
│─────────────────────────────│
│ - id: str (optional)         │
│ - subject: str               │
│ - body: str                  │
│ - recipient_email: EmailStr  │
│ - recipient_id: str          │
│ - campaign_id: str (FK)      │◄──────────┐
│ - sequence_step: int (1-20)  │           │
│ - segment: str               │           │
│ - sent_at: datetime          │           │
│ - opened_at: datetime        │           │
│ - clicked_at: datetime       │           │
│ - converted_at: datetime     │           │
└──────────────────────────────┘           │
         ▲                                  │
         │                                  │
         └──────────┬───────────────────────┘

┌──────────────────────────────┐
│ EmailCampaign                │
│─────────────────────────────│
│ - id: str                    │
│ - name: str                  │
│ - description: str           │
│ - emails: List[Email] ──────►├── (1 to many)
│ - target_segment: str        │
│ - upsell_type: str (optional)│
│ - created_at: datetime       │
│ - sent_at: datetime          │
│ - is_abtest: bool            │
└──────────────────────────────┘
         ▲
         │
         ├─────────────────────────┐
         │                         │
┌────────┴─────────┐      ┌────────┴──────────┐
│ EmailAnalytics   │      │ ABTestResult      │
│─────────────────│      │──────────────────│
│ - campaign_id──►├──FK  │ - test_id: str    │
│ - total_sent    │      │ - campaign_a_id──┼─FK
│ - total_opened  │      │ - campaign_b_id──┼─FK
│ - total_clicked │      │ - winner_id ─────┼─FK
│ - total_converti│      │ - open_rate_a    │
│ - open_rate     │      │ - open_rate_b    │
│ - click_rate    │      │ - is_significant │
│ - conversion_rat│      │ - evaluated_at   │
│ - last_updated  │      └──────────────────┘
└─────────────────┘

┌──────────────────────────────┐
│ StripeEvent                  │
│─────────────────────────────│
│ - event_id: str              │
│ - event_type: str            │
│ - customer_id: str           │
│ - subscription_id: str       │
│ - tier: str (phoenix/etc)    │
│ - received_at: datetime      │
│ - processed: bool            │
└──────────────────────────────┘

┌──────────────────────────────┐
│ WeeklyReport                 │
│─────────────────────────────│
│ - week_ending: datetime      │
│ - total_emails_sent: int     │
│ - avg_open_rate: float       │
│ - avg_ctr: float             │
│ - avg_conversion_rate: float │
│ - top_campaign_id: str (FK)  │
│ - bottom_campaign_id: str(FK)│
│ - subject_line_suggestions   │
│ - underperf_campaigns: List  │
└──────────────────────────────┘

Database Tables (SQLite):
┌────────────────────┐  ┌────────────────────┐  ┌─────────────────┐
│ email_opens        │  │ email_clicks       │  │ email_conversio │
├────────────────────┤  ├────────────────────┤  ├─────────────────┤
│ email_id (PK)      │  │ email_id (PK)      │  │ email_id (PK)   │
│ contact_id (PK)    │  │ contact_id (PK)    │  │ contact_id (PK) │
│ timestamp          │  │ link (PK)          │  │ type (PK)       │
│                    │  │ timestamp          │  │ timestamp       │
│ (1 row per open)   │  │                    │  │                 │
│                    │  │ (1 row per click)  │  │ (1 row per conv)│
└────────────────────┘  └────────────────────┘  └─────────────────┘

        │                       │                      │
        └───────────┬───────────┴──────────┬───────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ EmailAnalytics          │
        │ (aggregated from above) │
        │                         │
        │ open_rate =             │
        │  count(opens) /         │
        │  total_sent             │
        └─────────────────────────┘
```

---

## 9. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │  Config      │
                         │  (.env)      │
                         └────────┬─────┘
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
         ┌────────▼────────┐ ┌────▼─────────┐ ┌──▼──────────┐
         │ OpenAI API Key  │ │ CRM Creds    │ │ Stripe Key  │
         │ sk-...          │ │ hubspot/ck   │ │ sk_...      │
         └─────────────────┘ └──────────────┘ └─────────────┘
                  │                  │               │
                  └──────────┬────────┴───────┬──────┘
                             │                │
                    ┌────────▼────────────┐   │
                    │ EmailIntelligence   │   │
                    │ Agent               │   │
                    │ (Main Process)      │   │
                    └────────┬────────────┘   │
                             │                │
         ┌───────────────────┼────────────────┴──────────┐
         │                   │                           │
    ┌────▼──────┐     ┌──────▼──────┐     ┌────────────┐│
    │ CRM Clients│     │ Email Gen   │     │ Webhook    ││
    │ (HubSpot/CK)    │ + Guardrails│     │ Server     ││
    └────┬──────┘     └──────┬──────┘     └────┬───────┘│
         │                   │                  │       │
         │   REST/HTTP       │   YAML Config    │       │
         │                   │                  │       │
    ┌────▼────────────────────────────────────────────┐ │
    │ HubSpot/ConvertKit API                          │ │
    │                                                 │ │
    │ - Contacts management                          │ │
    │ - Campaign creation                            │ │
    │ - Analytics retrieval                          │ │
    └─────────────────────────────────────────────────┘ │
                                                        │
    ┌───────────────────────────────────────────────────┘
    │
    │ POST /webhooks/stripe (FastAPI)
    │ :8000
    │
    ▼
┌──────────────────────────┐
│ Stripe Event Webhooks    │
│ - subscription events    │
│ - payment events         │
│ - invoice events         │
└──────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ SQLite Database                                      │
│ - stripe_events (deduplication)                     │
│ - email_opens (tracking)                            │
│ - email_clicks (tracking)                           │
│ - email_conversions (tracking)                      │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Email Service (HubSpot/ConvertKit)                  │
│ - Embedded tracking pixels                          │
│ - Click wrapper URLs                                │
│ - Delivery status                                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ User Interactions                                    │
│ - Email open (pixel fired)                          │
│ - Link click (click wrapper triggered)              │
│ - Conversion event (user action tracked)            │
└──────────────────────────────────────────────────────┘
```

---

## 10. Error Handling & Recovery Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              ERROR HANDLING & RECOVERY FLOW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐
│ GuardrailViolationError     │
├─────────────────────────────┤
│ Triggered by:               │
│ - Medical claims            │
│ - Religious framing         │
│ - Guarantee language        │
│ - Therapy replacement       │
│                             │
│ Action:                     │
│ - Raise exception           │
│ - Log violation details     │
│ - Mark for human review     │
│ - Do NOT send email         │
│                             │
│ Human Resolution:           │
│ - Review flagged content    │
│ - Regenerate with feedback  │
│ - Approve & retry           │
└─────────────────────────────┘

┌─────────────────────────────┐
│ CRMError                    │
├─────────────────────────────┤
│ Triggered by:               │
│ - API 4xx/5xx response      │
│ - Network timeout           │
│ - Invalid credentials       │
│                             │
│ Action:                     │
│ - Log error with details    │
│ - If 429 (rate limit):      │
│   └─ Wait 1 second          │
│   └─ Retry once             │
│ - If other: abort & fail    │
│                             │
│ Recovery:                   │
│ - Check API key             │
│ - Verify network            │
│ - Retry operation           │
└─────────────────────────────┘

┌──────────────────────────────┐
│ WebhookValidationError       │
├──────────────────────────────┤
│ Triggered by:                │
│ - Invalid HMAC signature     │
│ - Timestamp too old (>5 min) │
│ - Malformed header           │
│                              │
│ Action:                      │
│ - Log security violation     │
│ - Return HTTP 400            │
│ - Do NOT process event       │
│                              │
│ Recovery:                    │
│ - Verify Stripe key          │
│ - Check system clock sync    │
│ - Stripe may retry           │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Database Errors              │
├──────────────────────────────┤
│ Triggered by:                │
│ - SQLite lock                │
│ - Insert/update failures     │
│ - Connection issues          │
│                              │
│ Action:                      │
│ - Log error                  │
│ - For non-critical: silently │
│   continue (tracking loss OK)│
│ - For critical: raise        │
│                              │
│ Recovery:                    │
│ - Check DB file permissions  │
│ - Verify disk space          │
│ - Reinitialize if corrupted  │
└──────────────────────────────┘

Overall Flow:
Try
├─ Execute operation
├─ Catch specific exception
├─ Log error details
├─ Alert if critical
├─ Attempt recovery
└─ Either succeed or fail gracefully
```

