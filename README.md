# 🛡️ Deadline Guardian Agent

An intelligent, AI-powered agent that monitors project deadlines, identifies risks, and provides strategic recommendations. It goes beyond simple date checking by understanding **dependencies**, **bottlenecks**, and **contextual urgency**.

## 🌐 Live Deployment

**Base URL**: `https://deadlinegaurdianagent-production.up.railway.app`

**Endpoints**:
- **Root**: `https://deadlinegaurdianagent-production.up.railway.app/`
- **Health Check**: `https://deadlinegaurdianagent-production.up.railway.app/health`
- **Main Handler**: `https://deadlinegaurdianagent-production.up.railway.app/handle`

## ✨ Features

- **🧠 AI-Powered Analysis**: Uses **Google Gemini Flash 2.0** (via OpenRouter) to understand task descriptions and urgency.
- **🕸️ Dependency Graph**: Automatically builds a dependency graph to identify blocked tasks.
- **⛔ Cascading Risk Detection**: Flags tasks as **BLOCKED** if their dependencies are overdue, even if the task itself is not due yet.
- **🚦 Bottleneck Identification**: Detects tasks that are holding up multiple other tasks.
- **📊 Smart Reporting**: Generates a human-readable report with risk levels (CRITICAL, HIGH, MEDIUM, LOW, BLOCKED).

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (Local or Atlas)
- OpenRouter API Key (Free)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/SaimZia/Deadline_gaurdian_agent.git
    cd Deadline_gaurdian_agent
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file:
    ```env
    MONGO_URI=mongodb://localhost:27017/
    DB_NAME=task_management
    COLLECTION_NAME=tasks
    PORT=8001
    OPENROUTER_API_KEY=your_key_here
    OPENROUTER_MODEL=google/gemini-2.0-flash-lite-preview-02-05:free
    ```

4.  **Run the Agent**:
    ```bash
    python app.py
    ```

## 📡 API Usage

The agent follows the **Supervisor Handshake Contract**.

### Endpoint: `POST /handle`

**Request**:
```json
{
  "request_id": "req-1",
  "agent_name": "deadline_guardian_agent",
  "intent": "deadline.monitor",
  "input": { "text": "check deadlines" },
  "context": { "user_id": "user1" }
}
```

**Response**:
```json
{
  "status": "success",
  "output": {
    "result": "📊 Advanced Deadline Report\n\nTotal Tasks: 10\nBottlenecks: 1\n...",
    "details": "Analyzed 10 tasks. 2 blocked tasks identified."
  }
}
```

## 🧪 Testing

Run the included test suite to verify logic:
```bash
python test_dependencies.py  # Test dependency graph logic
python test_ai_integration.py # Test AI integration (mocked)
```

## 📦 Deployment

Ready to deploy? Check out [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for instructions on deploying to Render or Railway.
