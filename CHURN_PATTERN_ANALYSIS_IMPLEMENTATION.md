# Churn Pattern Analysis Implementation

## Overview

Successfully replaced the **Patient Retention Status** section with a true diagnostic analytics feature: **Patient Churn Pattern Analysis**. This change addresses the question "When and why do customers stop returning?" by categorizing patients based on their visit history and engagement patterns.

## What Changed

### 1. Backend Changes (owner/views.py)

#### Added Max Import

```python
from django.db.models import Q, Count, Sum, Max  # Added Max for last_visit calculation
```

#### New Churn Pattern Calculation (Lines 181-219)

```python
# Calculate churn patterns - diagnostic analytics showing WHY patients leave
patients_with_visits = User.objects.filter(
    user_type='patient',
    appointments__status='completed'
).annotate(
    visit_count=Count('appointments', filter=Q(appointments__status='completed')),
    last_visit=Max('appointments__appointment_date', filter=Q(appointments__status='completed'))
).distinct()

# Four churn segments:
- one_time_customers: Exactly 1 completed visit
- early_dropoff: 2-3 visits, haven't returned in 90+ days
- lost_regulars: 4+ visits, haven't returned in 120+ days
- active_regulars: 4+ visits, returned within 120 days
```

#### Dynamic Insights Logic (Lines 373-404)

Analyzes churn patterns to determine:

- **Primary churn segment**: Identifies which churn pattern is most prevalent
- **Churn message**: Dynamic message based on the primary segment
- **Churn action**: Specific recommendations for addressing the churn pattern

**Insight Examples:**

- **One-time customers dominant**: "CRITICAL: X customers left after first visit - poor first impression" → Audit first-visit experience
- **Early dropoff dominant**: "WARNING: X customers dropped off after 2-3 visits - pricing or quality issue" → Review pricing and gather feedback
- **Lost regulars dominant**: "ATTENTION: X regular customers stopped returning - competition or life changes" → Launch re-engagement campaign
- **Active regulars dominant**: "EXCELLENT: X active regular customers maintain strong loyalty" → Continue retention strategies

#### Updated Context Dictionary (Line 453)

Added `churn_patterns` to template context for chart rendering.

#### Updated Analytics Insights (Lines 435-437)

Added three new fields:

```python
'churn_primary_segment': churn_primary_segment,
'churn_message': churn_message,
'churn_action': churn_action,
```

---

### 2. Frontend Changes (templates/owner/dashboard.html)

#### Section Title & Subtitle (Lines 568-572)

**Before:**

```html
<i class="fas fa-user-minus"></i> Patient Retention Status
<p>Why are customers not coming back?</p>
```

**After:**

```html
<i class="fas fa-user-minus"></i> Patient Churn Pattern Analysis
<p>When and why do customers stop returning?</p>
```

#### Table Structure (Lines 580-618)

**Columns:**
| Churn Pattern | Count | Likely Reason | Recommended Action |

**Rows with Color-Coded Backgrounds:**

1. **One-Time Customers** (Red background #ffe7e7)

   - Badge: Red (#dc3545)
   - Likely Reason: Poor first experience
   - Action: High Priority

2. **Early Dropoff** (Light orange background #fff3cd)

   - Badge: Orange (#fd7e14)
   - Likely Reason: Pricing or quality issue
   - Action: Medium Priority

3. **Lost Regulars** (Lightest yellow background #fff9e5)

   - Badge: Yellow (#ffc107)
   - Likely Reason: Competition or life change
   - Action: Re-engagement

4. **Active Regulars** (Light green background #e7f9f0)
   - Badge: Green (#28a745)
   - Likely Reason: High satisfaction
   - Action: Maintain

#### Dynamic Insight Card (Lines 621-634)

- Changes color based on `analytics_insights.churn_primary_segment`
- Green (active_regulars), Yellow (lost_regulars), Red (one-time/early_dropoff)
- Displays `churn_message` and `churn_action` dynamically

#### Updated Doughnut Chart JavaScript (Lines 1064-1114)

**Before:**

```javascript
const data = [activePatients, atRiskPatients, newPatients, inactivePatients];
const labels = [
  "Active Patients",
  "At-Risk Patients",
  "New Patients (30d)",
  "Inactive Patients",
];
const colors = ["#28a745", "#fd7e14", "#ffc107", "#6c757d"];
```

**After:**

```javascript
const data = [oneTimeCustomers, earlyDropoff, lostRegulars, activeRegulars];
const labels = [
  "One-Time Customers",
  "Early Dropoff (2-3 visits)",
  "Lost Regulars (4+ visits)",
  "Active Regulars",
];
const colors = ["#dc3545", "#fd7e14", "#ffc107", "#28a745"]; // Red, Orange, Yellow, Green
```

---

## Why This Change Matters

### Before: Patient Retention (Descriptive Analytics)

**What it showed:** Active/At-Risk/New/Inactive patient counts
**Problem:** Partially descriptive - it showed WHAT segments exist but didn't explain WHY patients leave

### After: Churn Pattern Analysis (Diagnostic Analytics)

**What it shows:** When in the customer journey patients churn and why
**Solution:** True diagnostic analytics answering "WHY are customers not coming back?"

### Business Value

1. **Actionable Insights**: Each churn segment has specific recommended actions
2. **Early Detection**: Identifies if the problem is first-visit experience (one-time), value proposition (early dropoff), or competition (lost regulars)
3. **Resource Prioritization**: Red/Orange/Yellow/Green color coding shows which churn segment needs immediate attention
4. **Data-Driven Decisions**: Dynamic insights change based on actual patient behavior patterns

---

## Data Sources

- **Patient Visit History**: Uses completed appointments to count total visits per patient
- **Recency Analysis**: Tracks `last_visit` date to determine if patients have churned
- **Visit Count Thresholds**:
  - 1 visit only → One-time customer
  - 2-3 visits + 90+ days since last visit → Early dropoff
  - 4+ visits + 120+ days since last visit → Lost regular
  - 4+ visits + returned within 120 days → Active regular

---

## Testing Checklist

- [x] Server starts without errors
- [x] No syntax errors in Python code
- [ ] Navigate to owner dashboard
- [ ] Verify "Patient Churn Pattern Analysis" section renders
- [ ] Check doughnut chart displays four segments with correct colors
- [ ] Verify table shows all four churn patterns with counts
- [ ] Confirm dynamic insight card changes color based on primary churn segment
- [ ] Test with different data scenarios (high one-time customers, high lost regulars, etc.)

---

## Future Enhancements

1. **Trend Analysis**: Track churn patterns over time (month-over-month)
2. **Cohort Analysis**: Analyze churn by patient acquisition date
3. **Service-Specific Churn**: Which services have highest one-time customer rate?
4. **Automated Alerts**: Email notification when one-time customers exceed threshold
5. **Re-engagement Campaigns**: Automated email/SMS to lost regulars with offers
