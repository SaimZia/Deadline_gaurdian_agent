# Deployment & Testing Guide

## 1. 🚀 Where to Deploy

Since this is a **Flask (Python)** application, I recommend these free/cheap platforms:

### **Option A: Render (Recommended)**
- **Why**: Easiest setup, free tier available.
- **Steps**:
  1. Push your code to GitHub.
  2. Go to [render.com](https://render.com).
  3. Click **New +** -> **Web Service**.
  4. Connect your GitHub repo.
  5. **Build Command**: `pip install -r requirements.txt`
  6. **Start Command**: `gunicorn app:app` (You need to add `gunicorn` to requirements.txt first!)
  7. Add Environment Variables (`MONGO_URI`, `OPENROUTER_API_KEY`, etc.) in the dashboard.

### **Option B: Railway**
- **Why**: Very stable, good for MongoDB connectivity.
- **Steps**: Similar to Render, connect GitHub and it auto-detects Python.

---

## 2. 🌐 Endpoints

Once deployed, your **Base URL** will look like:
`https://deadline-guardian.onrender.com` (Example)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/`      | Root check (Returns "Agent is running") |
| `GET`  | `/health`| Health check (Database & AI status) |
| `POST` | `/handle`| **Main Agent Endpoint** (Use this for Supervisor) |

---

## 3. 📥 Input & Output Format

### **Input Format (JSON)**
Send this to `POST /handle`:

```json
{
  "request_id": "req-123",
  "agent_name": "deadline_guardian_agent",
  "intent": "deadline.monitor",
  "input": {
    "text": "check my deadlines"
  },
  "context": {
    "user_id": "user_001",
    "timestamp": "2025-11-29T12:00:00"
  }
}
```

### **Output Format (JSON)**
You will receive this:

```json
{
  "request_id": "req-123",
  "agent_name": "deadline_guardian_agent",
  "status": "success",
  "output": {
    "result": "📊 **Advanced Deadline Report**\n\nTotal Tasks: 5\nAt Risk: 2...",
    "confidence": 1.0,
    "details": "Analyzed 5 tasks. 1 bottleneck identified."
  },
  "error": null
}
```

---

## 4. 🧪 Postman Test Cases

Copy these JSON bodies directly into Postman.

### **Test Case 1: Standard Check**
**URL**: `[YOUR_URL]/handle`
**Method**: `POST`
**Body**:
```json
{
  "request_id": "test-01",
  "agent_name": "deadline_guardian_agent",
  "intent": "deadline.monitor",
  "input": { "text": "check status" },
  "context": { "user_id": "tester", "timestamp": "2025-11-29T10:00:00" }
}
```

### **Test Case 2: Invalid Intent (Error Check)**
**URL**: `[YOUR_URL]/handle`
**Method**: `POST`
**Body**:
```json
{
  "request_id": "test-02",
  "agent_name": "deadline_guardian_agent",
  "intent": "wrong.intent", 
  "input": { "text": "check status" },
  "context": { "user_id": "tester", "timestamp": "2025-11-29T10:00:00" }
}
```
*Expected Result*: `400 Bad Request` with error message.

### **Test Case 3: Health Check**
**URL**: `[YOUR_URL]/health`
**Method**: `GET`
*Expected Result*: `200 OK`
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "ai_enabled": true
}
```
