---
name: attendance-intelligence
description: Use when the user asks about attendance issues, staff behavior, specific staff tracking, or workforce irregularities.
---

# Attendance Intelligence & Staff Behavior Analysis

## Instructions

1. Resolve time:
   - If user says "today", "yesterday", etc.
     → call get_current_time
     → convert to YYYY-MM-DD

2. Determine scope:

   - If user mentions specific staff:
     → Resolve staff using get_staffs (ALWAYS)
     → If multiple matches → select best match or handle ambiguity

   - If no specific staff:
     → Perform overall attendance analysis

3. Fetch attendance data:
   - get_attendances_advanced (for current date)

4. Fetch historical comparison:
   - yesterday
   - last week (same day)

5. If staff-specific:
   - Fetch logs using get_attendance_logs

6. Analyze attendance:

   Identify:
   - Present vs absent
   - Sudden absences
   - Late check-ins
   - Missing check-outs
   - Low working hours
   - Excessive overtime

7. Analyze movement behavior (VERY IMPORTANT):

   From logs, identify:
   - Entry/exit frequency
   - Movement timing
   - Long inactivity gaps
   - Repeated or unusual movement patterns

8. Compare with historical data:

   - Changes vs yesterday
   - Changes vs last week
   - Consistency or irregularity in behavior

9. Detect anomalies:

   Highlight:
   - Staff with unusual attendance patterns
   - Sudden behavior changes
   - Suspicious movement or irregular activity

10. Provide insights:

   - What changed
   - Who is affected
   - What is abnormal
   - Possible operational impact