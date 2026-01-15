# Biz-Pulse Design Document

**Date:** 2026-01-13
**Status:** Approved

## Overview

Biz-Pulse is a customer analytics platform for small business owners. It helps them understand their customer base, identify growth opportunities, and take action to retain valuable customers.

## User Flow

```
Login → Upload CSV → Generate Insights (6 tabs)
```

### 1. Login Page
- Email (required)
- Business name (required)
- No password for MVP — simple identification only

### 2. Upload Page
- Drag & drop or browse for CSV file
- Preview: customer count, date range detected
- "Generate Insights" button

### 3. Insights Dashboard (6 tabs)

## CSV Data Format

Based on Square export format. Required columns:

| Column | Type | Purpose |
|--------|------|---------|
| `client_name` | string | Customer identifier |
| `start` | datetime | Appointment date |
| `status` | string | Filter to "accepted" only |
| `service` | string | Service name(s) |
| `email` | string | For outreach (optional) |
| `phone` | string | For WhatsApp outreach (optional) |

Pricing: For MVP, assume placeholder prices based on service type. Future: service-to-price mapping table.

---

## Tab 1: Segmentation Analysis

**Purpose:** Segment customers by visit frequency and show revenue contribution.

### Segments (from BarefootCare report)
- **Explorer:** 1-2 visits
- **Casual:** 3-8 visits
- **Regular:** 9-12 visits
- **Superuser:** 13+ visits

### UI Components
- Date range selector
- Key metrics cards: Total Customers, Revenue, Avg Visits, Avg LTV
- Pie chart: Customers by segment
- Bar chart: Revenue by segment
- Segment definitions reference

---

## Tab 2: Latent Demand (NBD Model)

**Purpose:** Estimate unobserved customers (market sizing).

### Model
Zero-Truncated Negative Binomial Distribution (ZT-NBD)

### UI Components
- Date range selector
- "The Big Picture" metrics: Observed, Potential, Market Captured %
- Plain English explanation of market opportunity
- Bar chart: Actual vs Predicted visit frequencies
- "Customer Behavior Insights" section:
  - Heterogeneity scale (visual, not raw r value)
  - Plain English interpretation
  - Actionable takeaways
- Model reliability indicator (progress bar: Moderate/Good/Excellent)
- Expandable "Show technical details" for r, α, chi-square

### Plain English Translations
- Low r value → "Your customers are very different from each other"
- High f0 estimate → "X potential customers haven't discovered you yet"
- Poor model fit → "Treat estimates as directional, not exact"

---

## Tab 3: Retention & Churn History

**Purpose:** Identify at-risk customers and show retention patterns.

### UI Components
- Date range selector
- "Customers at Risk" cards: Overdue (30+ days), Slipping (60+ days), Lost (90+ days)
- Plain English summary
- At-risk customer table:
  - Name, Segment, Last Visit, Days Since, $Risk
  - Sortable by "Value at Risk"
  - Export CSV button
- Retention over time line chart
- Plain English insights:
  - % returning for second visit (vs last year)
  - Retention by segment
  - Biggest drop-off point

---

## Tab 4: Upgrade Suggestions

**Purpose:** Recommend actions to move customers up segments.

### UI Components
- Date range selector
- "Upgrade Opportunity" summary: revenue gain from converting X Casuals to Regulars
- Visual: Casual → Regular with $ difference
- "Best Candidates" table:
  - Name, Visits, Trend (accelerating/steady/flat), Likelihood
- Suggested actions with message templates:
  - For Casuals close to Regular
  - For Explorers who haven't returned
- Per-customer action buttons:
  - [📧 Send Email] → opens mailto: with pre-filled message
  - [💬 WhatsApp] → opens wa.me/ with pre-filled message
  - [✏️ Edit Message] → inline edit before sending
- Auto-generated coupon codes (customizable)

### Outreach Implementation
- Email: `mailto:email@example.com?subject=...&body=...`
- WhatsApp: `https://wa.me/14155550123?text=...`
- Opens user's default app — no backend required

---

## Tab 5: CLV Prediction (Gamma-Gamma)

**Purpose:** Predict customer lifetime value based on spending patterns.

### Model
Gamma-Gamma model for monetary value prediction

### UI Components
- Date range selector
- CLV Overview metrics: Average CLV, Top 10% CLV, Total Predicted
- Plain English summary
- CLV distribution histogram
- "Most Valuable Customers" table:
  - Name, Segment, Visits, Spend, CLV
  - Export CSV button
- "Hidden Gems" section:
  - High spend per visit, low frequency
  - "If Regular → CLV" projection
  - [📧 Reach out to Hidden Gems] button
- Expandable technical details

---

## Tab 6: Churn Prediction (BG/NBD)

**Purpose:** Predict when customers will churn and suggest prevention.

### Model
BG/NBD (Beta-Geometric/Negative Binomial Distribution) for P(alive)

### UI Components
- Date range selector
- Churn Risk Summary: Likely to Churn count, Revenue at Risk, % Still Active
- Plain English summary
- Scatter plot: Recency vs Frequency, colored by P(churn)
  - Red = probably gone
  - Yellow = worth reaching out
  - Green = healthy core
- "High-Value Customers at Risk" table:
  - Name, CLV, Last Visit, P(Churn)
  - Inline action buttons: [📧 Email] [💬 WhatsApp]
  - Export CSV
- Win-back message templates:
  - Per-customer send buttons
  - "Send to all X at-risk" bulk action
  - Editable template
- Expandable technical details

---

## Tech Stack

- **Framework:** Python + Streamlit (multi-page app)
- **Analytics:** `lifetimes` library (NBD, BG/NBD, Gamma-Gamma models)
- **Data:** pandas for CSV processing
- **Charts:** Streamlit native + plotly
- **Outreach:** mailto: and wa.me: links (no backend)

## File Structure

```
bizpulse/
├── app.py                      # Entry point, login page
├── pages/
│   ├── 1_📊_Segmentation.py
│   ├── 2_🎯_Latent_Demand.py
│   ├── 3_⚠️_Retention.py
│   ├── 4_💡_Upgrades.py
│   ├── 5_💎_CLV.py
│   └── 6_🚨_Churn.py
├── utils/
│   ├── data_loader.py          # CSV parsing, validation
│   ├── segmentation.py         # Segment assignment logic
│   ├── models.py               # NBD, BG/NBD, Gamma-Gamma fitting
│   ├── insights.py             # Plain English generators
│   └── outreach.py             # mailto/whatsapp URL builders
├── data/
│   └── uploads/                # Uploaded CSVs (session-based)
├── sample_data/
│   └── appointments_sample.csv # Demo data
└── requirements.txt
```

## Key Design Principles

1. **Plain English first** — Technical stats hidden behind expandable sections
2. **Actionable** — Every insight has a "do something" button
3. **Date range filtering** — Every tab supports time-based analysis
4. **Segment-aware** — Everything ties back to the 4 customer segments
5. **MVP mindset** — Local email/WhatsApp, no backend integrations yet

## Future Enhancements (Post-MVP)

- Service-to-price mapping UI
- SendGrid/Twilio integration for direct sending
- Square API integration for live data
- Multi-business support with authentication
- Scheduled reports via email
