import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "task_management")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tasks")
PORT = int(os.getenv("PORT", 8001))

# AI Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")

# Initialize OpenAI Client (for OpenRouter)
client = None
if OPENROUTER_API_KEY:
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    except Exception as e:
        print(f"⚠️ Failed to initialize AI client: {e}")

# MongoDB Connection
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Check connection
    mongo_client.admin.command('ping')
    print(f"✅ Connected to MongoDB: {DB_NAME}.{COLLECTION_NAME}")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    mongo_client = None
    db = None
    collection = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "agent": "deadline_guardian_agent",
        "timestamp": datetime.now().isoformat(),
        "mongodb": "connected" if mongo_client else "disconnected",
        "ai_enabled": bool(client)
    }
    return jsonify(status), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint to show agent is running."""
    return jsonify({
        "message": "Deadline Guardian Agent is running 🚀",
        "endpoints": {
            "health": "/health",
            "handle": "/handle"
        },
        "status": "online"
    }), 200

def calculate_risk_level(deadline_str, status):
    """Calculate risk level based on deadline and status."""
    if status.lower() in ["done", "completed"]:
        return "COMPLETED", 0

    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
        now = datetime.now()
        days_remaining = (deadline - now).days
        
        if days_remaining < 0:
            return "CRITICAL", days_remaining
        elif days_remaining < 1:
            return "HIGH", days_remaining
        elif days_remaining < 3:
            return "MEDIUM", days_remaining
        else:
            return "LOW", days_remaining
    except ValueError:
        return "UNKNOWN", 0

def format_time_remaining(days):
    """Format time remaining in a human-readable way."""
    if days < 0:
        return f"OVERDUE by {abs(days)} day(s)"
    elif days == 0:
        return "Due TODAY"
    else:
        return f"{days} day(s)"

def build_dependency_graph(tasks):
    """
    Build a dependency graph from tasks.
    Returns:
        graph: Dict mapping task_id -> list of dependent task_ids (reverse dependencies)
        status_map: Dict mapping task_id -> task_status
        risk_map: Dict mapping task_id -> risk_level
    """
    graph = {}
    status_map = {}
    risk_map = {}
    
    # Initialize graph
    for task in tasks:
        t_id = task.get('task_id')
        graph[t_id] = []
        status_map[t_id] = task.get('task_status', 'todo')
        
        # Calculate initial risk
        risk, _ = calculate_risk_level(task.get('task_deadline', ''), task.get('task_status', ''))
        risk_map[t_id] = risk

    # Populate dependencies
    for task in tasks:
        t_id = task.get('task_id')
        depends_on = task.get('depends_on')
        
        if depends_on:
            # Handle comma-separated dependencies if string
            deps = [d.strip() for d in depends_on.split(',')] if isinstance(depends_on, str) else [depends_on]
            
            for dep_id in deps:
                if dep_id in graph:
                    graph[dep_id].append(t_id)
    
    return graph, status_map, risk_map

def analyze_cascading_risks(tasks):
    """
    Analyze tasks for cascading risks (blocked by overdue/critical tasks).
    Returns:
        blocked_tasks: List of task_ids that are blocked
        bottlenecks: List of task_ids that are blocking multiple tasks
    """
    graph, status_map, risk_map = build_dependency_graph(tasks)
    blocked_tasks = set()
    bottlenecks = []
    
    # Identify blocked tasks
    for task in tasks:
        t_id = task.get('task_id')
        depends_on = task.get('depends_on')
        
        if depends_on:
            deps = [d.strip() for d in depends_on.split(',')] if isinstance(depends_on, str) else [depends_on]
            for dep_id in deps:
                # If dependency is CRITICAL, OVERDUE, or HIGH risk, the dependent task is BLOCKED
                dep_risk = risk_map.get(dep_id)
                if dep_risk in ["CRITICAL", "HIGH"]:
                    blocked_tasks.add(t_id)
    
    # Identify bottlenecks (tasks blocking > 1 other task)
    for t_id, dependents in graph.items():
        if len(dependents) > 1:
            bottlenecks.append(t_id)
            
    return list(blocked_tasks), bottlenecks

def analyze_risks_with_llm(tasks, blocked_tasks, bottlenecks):
    """
    Analyze tasks using LLM with advanced dependency context.
    """
    if not client:
        return None

    # Prepare task summary for LLM
    task_summaries = []
    for task in tasks:
        t_id = task.get('task_id')
        is_blocked = "YES (BLOCKED)" if t_id in blocked_tasks else "NO"
        is_bottleneck = "YES (BOTTLENECK)" if t_id in bottlenecks else "NO"
        
        task_summaries.append(
            f"- ID: {t_id}\n"
            f"  Name: {task.get('task_name')}\n"
            f"  Status: {task.get('task_status')}\n"
            f"  Deadline: {task.get('task_deadline')}\n"
            f"  Blocked: {is_blocked}\n"
            f"  Bottleneck: {is_bottleneck}\n"
            f"  Description: {task.get('task_description', 'No description')}"
        )
    
    tasks_text = "\n".join(task_summaries)
    
    prompt = f"""
    You are a Senior Project Manager analyzing complex project risks.
    
    Analyze the following tasks, paying special attention to DEPENDENCIES and BOTTLENECKS.
    
    Key Analysis Points:
    1. **Cascading Risks**: Identify tasks blocked by high-risk dependencies.
    2. **Bottlenecks**: Flag tasks that are holding up multiple other tasks.
    3. **Strategic Prioritization**: Recommend focusing on clearing bottlenecks first.
    
    Tasks:
    {tasks_text}
    
    Return a JSON object with this structure:
    {{
        "risk_analysis": "Concise summary of risks, highlighting bottlenecks and blocked chains.",
        "strategic_recommendations": [
            "Actionable recommendation 1 (focus on bottlenecks)",
            "Actionable recommendation 2"
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful project management assistant. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"❌ AI Analysis failed: {e}")
        return None

@app.route('/handle', methods=['POST'])
def handle_request():
    """
    Main handler for the agent.
    Follows the supervisor handshake contract.
    """
    data = request.json
    
    if not data:
        return jsonify({
            "request_id": "unknown",
            "agent_name": "deadline_guardian_agent",
            "status": "error",
            "error": {
                "type": "invalid_request",
                "message": "Missing request body"
            }
        }), 400

    request_id = data.get('request_id')
    intent = data.get('intent')
    
    # Validate intent
    if intent != "deadline.monitor":
        return jsonify({
            "request_id": request_id,
            "agent_name": "deadline_guardian_agent",
            "status": "error",
            "error": {
                "type": "invalid_intent",
                "message": f"Unsupported intent: {intent}. Only 'deadline.monitor' is supported."
            }
        }), 400

    try:
        # Fetch tasks from MongoDB
        if collection is not None:
            tasks = list(collection.find({}))
        else:
            tasks = [] # Fallback if DB not connected

        # 1. Advanced Dependency Analysis
        blocked_tasks, bottlenecks = analyze_cascading_risks(tasks)

        # 2. Deterministic Analysis (Hard Logic)
        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "COMPLETED": 0, "UNKNOWN": 0, "BLOCKED": 0}
        analyzed_tasks = []
        
        for task in tasks:
            t_id = task.get('task_id')
            risk, days = calculate_risk_level(
                task.get('task_deadline', ''), 
                task.get('task_status', '')
            )
            
            # Override risk if blocked
            if t_id in blocked_tasks and risk not in ["CRITICAL", "COMPLETED"]:
                risk = "BLOCKED"
            
            risk_counts[risk] += 1
            
            analyzed_tasks.append({
                "id": t_id,
                "name": task.get('task_name'),
                "deadline": task.get('task_deadline'),
                "risk": risk,
                "days_remaining": days,
                "time_text": format_time_remaining(days),
                "is_bottleneck": t_id in bottlenecks
            })

        # 3. AI Analysis (Soft Logic)
        ai_insights = analyze_risks_with_llm(tasks, blocked_tasks, bottlenecks) if client and tasks else None

        # 4. Construct Response
        
        # Build text report
        report_lines = ["📊 **Advanced Deadline Report**\n"]
        report_lines.append(f"Total Tasks: {len(tasks)}")
        report_lines.append(f"At Risk: {risk_counts['CRITICAL'] + risk_counts['HIGH'] + risk_counts['BLOCKED']}")
        report_lines.append(f"Bottlenecks: {len(bottlenecks)}")
        report_lines.append(f"Blocked: {len(blocked_tasks)}\n")
        
        # Add AI Summary if available
        if ai_insights and "risk_analysis" in ai_insights:
            report_lines.append(f"🤖 **AI Analysis**: {ai_insights['risk_analysis']}\n")

        # List Critical/High/Blocked tasks
        if risk_counts['CRITICAL'] > 0:
            report_lines.append(f"🚨 **CRITICAL ({risk_counts['CRITICAL']})**:")
            for t in analyzed_tasks:
                if t['risk'] == 'CRITICAL':
                    bottleneck_tag = " [BOTTLENECK]" if t['is_bottleneck'] else ""
                    report_lines.append(f"  • [{t['id']}] {t['name']} - {t['time_text']}{bottleneck_tag}")
            report_lines.append("")

        if risk_counts['BLOCKED'] > 0:
            report_lines.append(f"⛔ **BLOCKED ({risk_counts['BLOCKED']})**:")
            for t in analyzed_tasks:
                if t['risk'] == 'BLOCKED':
                    report_lines.append(f"  • [{t['id']}] {t['name']} - Blocked by dependency")
            report_lines.append("")

        if risk_counts['HIGH'] > 0:
            report_lines.append(f"⚠️ **HIGH RISK ({risk_counts['HIGH']})**:")
            for t in analyzed_tasks:
                if t['risk'] == 'HIGH':
                    bottleneck_tag = " [BOTTLENECK]" if t['is_bottleneck'] else ""
                    report_lines.append(f"  • [{t['id']}] {t['name']} - {t['time_text']}{bottleneck_tag}")
            report_lines.append("")
            
        # Add AI Recommendations if available
        if ai_insights and "strategic_recommendations" in ai_insights:
            report_lines.append("💡 **Strategic Recommendations**:")
            for rec in ai_insights['strategic_recommendations']:
                report_lines.append(f"  • {rec}")
        elif not ai_insights and risk_counts['CRITICAL'] > 0:
             report_lines.append("💡 **Recommendation**: Immediate action required on overdue tasks!")

        result_text = "\n".join(report_lines)
        
        details_text = f"Analyzed {len(tasks)} tasks. {len(bottlenecks)} bottlenecks identified."
        if ai_insights:
            details_text += " AI analysis included."

        return jsonify({
            "request_id": request_id,
            "agent_name": "deadline_guardian_agent",
            "status": "success",
            "output": {
                "result": result_text,
                "confidence": 1.0,
                "details": details_text
            },
            "error": None
        })

    except Exception as e:
        return jsonify({
            "request_id": request_id,
            "agent_name": "deadline_guardian_agent",
            "status": "error",
            "error": {
                "type": "processing_error",
                "message": f"Failed to analyze deadlines: {str(e)}"
            }
        }), 500

if __name__ == '__main__':
    print(f"🚀 Deadline Guardian Agent running on port {PORT}")
    if client:
        print(f"🤖 AI Enabled: {OPENROUTER_MODEL}")
    else:
        print("⚠️  AI Disabled (Missing OPENROUTER_API_KEY)")
    
    app.run(host='0.0.0.0', port=PORT)
