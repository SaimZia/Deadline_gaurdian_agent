# 🧪 Postman Test Scenarios (Custom Data)

Based on the data you provided, here is the exact test case to run in Postman and the **Expected Result** you should see from the agent.

## 1. The Setup
Ensure your MongoDB has the data you shared.
*   **Task 15** ("Schedule Meeting With CTO") is due **2025-11-29** (Today).
*   **Task 12/13** are due **2025-12-15** (Future).
*   **Task 14** has **no deadline**.

## 2. The Request
**Method**: `POST`
**URL**: `http://localhost:8001/handle` (or your deployed URL)
**Headers**: `Content-Type: application/json`

**Body (JSON)**:
```json
{
  "request_id": "test-custom-data-01",
  "agent_name": "deadline_guardian_agent",
  "intent": "deadline.monitor",
  "input": {
    "text": "analyze my tasks"
  },
  "context": {
    "user_id": "saim_zia",
    "timestamp": "2025-11-29T21:45:00"
  }
}
```

## 3. Expected Response
The agent will analyze your specific tasks. Here is what the JSON output will look like:

```json
{
    "request_id": "test-custom-data-01",
    "agent_name": "deadline_guardian_agent",
    "status": "success",
    "output": {
        "result": "📊 **Advanced Deadline Report**\n\nTotal Tasks: 5\nAt Risk: 1\nBottlenecks: 0\nBlocked: 0\n\n🤖 **AI Analysis**: [AI will likely flag the CTO meeting as urgent]\n\n🚨 **CRITICAL (1)**:\n  • [15] Schedule Meeting With CTO - OVERDUE by 1 day(s)\n\n📌 **MEDIUM/LOW RISK**:\n  • [12] Check Deadline Risks - 15 day(s)\n  • [13] Implement User Authentication System - 15 day(s)\n\n💡 **Recommendation**: Immediate action required on overdue tasks!",
        "confidence": 1.0,
        "details": "Analyzed 5 tasks. 1 tasks require immediate attention. AI analysis included."
    },
    "error": null
}
```

## 4. Why this result?

1.  **Task 15 (Meeting with CTO)**:
    *   Deadline: `2025-11-29`
    *   Current Time: `2025-11-29 21:45`
    *   Logic: The deadline (midnight) has passed by ~21 hours.
    *   **Result**: **CRITICAL / OVERDUE**.

2.  **Task 14 (Summarize Document)**:
    *   Deadline: `""` (Empty)
    *   **Result**: **UNKNOWN** (Won't appear in risk lists, but counted in total).

3.  **Task 12 & 13**:
    *   Deadline: `2025-12-15`
    *   **Result**: **LOW RISK** (Safe).

4.  **AI Insights**:
    *   The AI will read "Meeting with CTO at sharp 9 PM" and likely scream that you are late! 🚨
