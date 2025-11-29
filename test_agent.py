"""
Test script for Deadline Guardian Agent
"""
import requests
import json

# Test 1: Health Check
print("=" * 60)
print("TEST 1: Health Check")
print("=" * 60)

try:
    response = requests.get("http://localhost:8001/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("✅ Health check passed!\n")
except Exception as e:
    print(f"❌ Health check failed: {e}\n")

# Test 2: Deadline Monitoring Request
print("=" * 60)
print("TEST 2: Deadline Monitoring Request")
print("=" * 60)

payload = {
    "request_id": "test-123",
    "agent_name": "deadline_guardian_agent",
    "intent": "deadline.monitor",
    "input": {
        "text": "check my deadlines"
    },
    "context": {
        "user_id": "test_user",
        "timestamp": "2025-11-29T17:30:00"
    }
}

try:
    response = requests.post(
        "http://localhost:8001/handle",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"\nFull Response:")
    print(json.dumps(result, indent=2))
    
    if result.get("status") == "success":
        print("\n" + "=" * 60)
        print("DEADLINE REPORT:")
        print("=" * 60)
        print(result["output"]["result"])
        print("\n" + "=" * 60)
        print(f"Confidence: {result['output']['confidence']}")
        print(f"Details: {result['output']['details']}")
        print("=" * 60)
        print("\n✅ Deadline monitoring test passed!")
    else:
        print(f"\n❌ Request failed with error: {result.get('error')}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test 3: Invalid Intent
print("\n" + "=" * 60)
print("TEST 3: Invalid Intent (Error Handling)")
print("=" * 60)

invalid_payload = {
    "request_id": "test-456",
    "agent_name": "deadline_guardian_agent",
    "intent": "invalid.intent",
    "input": {"text": "test"},
    "context": {"user_id": "test", "timestamp": "2025-11-29T17:30:00"}
}

try:
    response = requests.post(
        "http://localhost:8001/handle",
        json=invalid_payload
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get("status") == "error":
        print("\n✅ Error handling test passed - correctly rejected invalid intent!")
    else:
        print("\n❌ Error handling test failed - should have rejected invalid intent")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
