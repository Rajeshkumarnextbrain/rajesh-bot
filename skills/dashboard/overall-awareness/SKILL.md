---
name: overall-awareness
description: Use when the user asks for system status, summary, trends, comparisons, or what is happening over time.
---

# Overall Awareness & Trend Analysis

## Instructions

1. Resolve time:
   - If user says "today", "yesterday", "this week"
     → resolve appropriately
   - If not specified → assume today

2. Determine comparison scope:
   - Default:
     → today vs yesterday
     → today vs same day last week
   - If user asks trend:
     → include week vs last week

3. Fetch current data:
   - get_event_counts
   - get_vehicle_counts
   - get_crowd_counts

4. Fetch historical data:
   - yesterday (same metrics)
   - last week (same day or range)

5. Compare data:

   Identify:
   - Increases or decreases
   - Growth or decline trends
   - Stable vs unstable patterns
   - Repeating spikes or patterns

6. Detect anomalies:

   Highlight:
   - Sudden spikes
   - Unusual drops
   - Rare or unexpected events

7. Identify key insights:

   - Most active category
   - Significant changes over time
   - Behavior differences vs yesterday and last week
   - Any consistent trends

8. Provide reasoning:

   - Explain what changed
   - Explain why it may have changed (if possible)
   - Highlight anything unusual or important