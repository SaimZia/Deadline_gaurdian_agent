"""
MongoDB Connection and Data Verification Test
Tests if MongoDB connection is stable and can fetch task data
"""
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("MongoDB Connection & Data Verification Test")
print("=" * 70)

# Get MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "task_management")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tasks")

print(f"\nConfiguration:")
print(f"  MongoDB URI: {MONGO_URI[:50]}..." if len(MONGO_URI) > 50 else f"  MongoDB URI: {MONGO_URI}")
print(f"  Database: {DB_NAME}")
print(f"  Collection: {COLLECTION_NAME}")

# Test 1: Connection Test
print("\n" + "=" * 70)
print("TEST 1: MongoDB Connection")
print("=" * 70)

try:
    print("Attempting to connect to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Force connection by pinging the server
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
    
    # List available databases
    db_list = client.list_database_names()
    print(f"\nAvailable databases: {', '.join(db_list)}")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("\nPossible issues:")
    print("  1. MongoDB server is not running")
    print("  2. Incorrect MONGO_URI in .env file")
    print("  3. Network/firewall issues")
    print("  4. Authentication credentials incorrect")
    exit(1)

# Test 2: Database Access
print("\n" + "=" * 70)
print("TEST 2: Database Access")
print("=" * 70)

try:
    db = client[DB_NAME]
    print(f"✅ Accessing database: {DB_NAME}")
    
    # List collections in the database
    collections = db.list_collection_names()
    print(f"\nCollections in '{DB_NAME}': {', '.join(collections) if collections else 'None'}")
    
    if COLLECTION_NAME not in collections:
        print(f"⚠️  Warning: Collection '{COLLECTION_NAME}' not found!")
        print(f"   Available collections: {collections}")
    else:
        print(f"✅ Collection '{COLLECTION_NAME}' exists")
        
except Exception as e:
    print(f"❌ Database access failed: {e}")
    exit(1)

# Test 3: Fetch Tasks
print("\n" + "=" * 70)
print("TEST 3: Fetch Tasks from Collection")
print("=" * 70)

try:
    tasks_collection = db[COLLECTION_NAME]
    
    # Count total tasks
    total_count = tasks_collection.count_documents({})
    print(f"\nTotal tasks in collection: {total_count}")
    
    if total_count == 0:
        print("⚠️  No tasks found in the collection!")
        print("   The collection exists but is empty.")
        exit(0)
    
    # Fetch all tasks
    print(f"\n✅ Fetching {total_count} tasks...")
    tasks = list(tasks_collection.find())
    
    print(f"✅ Successfully fetched {len(tasks)} tasks!")
    
except Exception as e:
    print(f"❌ Failed to fetch tasks: {e}")
    exit(1)

# Test 4: Display Task Details
print("\n" + "=" * 70)
print("TEST 4: Task Data Validation")
print("=" * 70)

print(f"\nDisplaying all {len(tasks)} tasks:\n")

for i, task in enumerate(tasks, 1):
    print(f"Task {i}:")
    print(f"  _id: {task.get('_id')}")
    print(f"  task_id: {task.get('task_id')}")
    print(f"  task_name: {task.get('task_name')}")
    print(f"  task_status: {task.get('task_status')}")
    print(f"  task_deadline: {task.get('task_deadline')}")
    print(f"  task_description: {task.get('task_description', '')[:60]}...")
    print(f"  depends_on: {task.get('depends_on')}")
    print()

# Test 5: Validate Task Structure
print("=" * 70)
print("TEST 5: Task Structure Validation")
print("=" * 70)

required_fields = ['task_id', 'task_name', 'task_status', 'task_deadline']
all_valid = True

for i, task in enumerate(tasks, 1):
    missing_fields = [field for field in required_fields if field not in task]
    
    if missing_fields:
        print(f"❌ Task {i} (ID: {task.get('task_id', 'unknown')}) missing fields: {missing_fields}")
        all_valid = False
    else:
        print(f"✅ Task {i} (ID: {task.get('task_id')}) has all required fields")

if all_valid:
    print(f"\n✅ All {len(tasks)} tasks have valid structure!")
else:
    print("\n⚠️  Some tasks have missing fields")

# Test 6: Deadline Analysis Preview
print("\n" + "=" * 70)
print("TEST 6: Deadline Analysis Preview")
print("=" * 70)

now = datetime.now()
print(f"\nCurrent date/time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

for task in tasks:
    task_id = task.get('task_id', 'unknown')
    task_name = task.get('task_name', 'Unknown')
    task_deadline = task.get('task_deadline', '')
    task_status = task.get('task_status', 'unknown')
    
    try:
        deadline = datetime.strptime(task_deadline, "%Y-%m-%d")
        time_remaining = deadline - now
        days = time_remaining.days
        
        if task_status == "done":
            risk = "COMPLETED"
        elif days < 0:
            risk = "CRITICAL (OVERDUE)"
        elif days < 1:
            risk = "HIGH"
        elif days < 3:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        print(f"[{task_id}] {task_name}")
        print(f"  Deadline: {task_deadline} | Days remaining: {days} | Risk: {risk}")
        
    except Exception as e:
        print(f"[{task_id}] {task_name}")
        print(f"  ⚠️  Invalid deadline format: {task_deadline}")
    
    print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\n✅ MongoDB Connection: STABLE")
print(f"✅ Database Access: SUCCESS")
print(f"✅ Tasks Fetched: {len(tasks)}")
print(f"✅ Data Structure: {'VALID' if all_valid else 'NEEDS REVIEW'}")

print("\n" + "=" * 70)
print("MongoDB connection is stable and data can be fetched successfully!")
print("=" * 70)

# Close connection
client.close()
print("\n✅ MongoDB connection closed cleanly")
