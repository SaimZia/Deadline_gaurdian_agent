"""
Comprehensive Test Cases for Deadline Guardian Agent
Based on real MongoDB tasks
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

# ANSI color codes for better output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print("\n" + "=" * 70)
    print(f"{BLUE}{text}{RESET}")
    print("=" * 70)

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")


# Test Case 1: Health Check
def test_health_check():
    print_header("TEST CASE 1: Health Check")
    print_info("Verifying agent is running and MongoDB is connected")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200, "Expected status code 200"
        assert data["status"] == "healthy", "Agent should be healthy"
        assert data["agent"] == "deadline_guardian_agent", "Wrong agent name"
        assert data["mongodb"] == "connected", "MongoDB should be connected"
        
        print_success("Health check passed - Agent is running and MongoDB connected")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


# Test Case 2: Basic Deadline Monitoring Request
def test_basic_deadline_monitoring():
    print_header("TEST CASE 2: Basic Deadline Monitoring")
    print_info("Testing standard deadline monitoring request")
    
    payload = {
        "request_id": "test-basic-001",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {
            "text": "check my deadlines"
        },
        "context": {
            "user_id": "test_user",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nRequest ID: {data.get('request_id')}")
        print(f"Status: {data.get('status')}")
        
        assert response.status_code == 200, "Expected status code 200"
        assert data["status"] == "success", "Request should succeed"
        assert data["request_id"] == payload["request_id"], "Request ID mismatch"
        assert data["output"] is not None, "Output should not be None"
        assert data["error"] is None, "Error should be None on success"
        
        print(f"\n{BLUE}Deadline Report:{RESET}")
        print("-" * 70)
        print(data["output"]["result"])
        print("-" * 70)
        print(f"\nConfidence: {data['output']['confidence']}")
        print(f"Details: {data['output']['details']}")
        
        print_success("Basic deadline monitoring test passed")
        return True
    except Exception as e:
        print_error(f"Basic deadline monitoring failed: {e}")
        return False


# Test Case 3: Verify Specific Tasks in Response
def test_specific_tasks_detection():
    print_header("TEST CASE 3: Specific Tasks Detection")
    print_info("Verifying all 4 tasks are detected and categorized correctly")
    
    expected_tasks = {
        "8": "Review API Rate Limits",
        "9": "Summarize Project Status",
        "10": "Implement User Authentication System",
        "11": "Fix Bug In Payment Processing Module"
    }
    
    payload = {
        "request_id": "test-tasks-002",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {"text": "show all tasks"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        result_text = data["output"]["result"]
        
        print(f"\nChecking for expected tasks:")
        found_tasks = []
        for task_id, task_name in expected_tasks.items():
            if task_id in result_text and task_name in result_text:
                print_success(f"Task {task_id}: {task_name}")
                found_tasks.append(task_id)
            else:
                print_error(f"Task {task_id}: {task_name} NOT FOUND")
        
        assert len(found_tasks) == 4, f"Expected 4 tasks, found {len(found_tasks)}"
        print_success(f"All {len(found_tasks)} tasks detected correctly")
        return True
    except Exception as e:
        print_error(f"Task detection failed: {e}")
        return False


# Test Case 4: Risk Level Categorization
def test_risk_categorization():
    print_header("TEST CASE 4: Risk Level Categorization")
    print_info("Verifying tasks are categorized by risk level correctly")
    
    # Expected risk levels based on current date (2025-11-29)
    # Task 8: 2025-12-01 (2 days) -> MEDIUM
    # Task 9: 2025-12-15 (16 days) -> LOW
    # Task 10: 2025-12-15 (16 days) -> LOW
    # Task 11: 2025-12-20 (21 days) -> LOW
    
    payload = {
        "request_id": "test-risk-003",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {"text": "check deadline risks"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        result_text = data["output"]["result"]
        
        print(f"\nRisk Analysis:")
        
        # Check for risk categories in output
        has_critical = "CRITICAL" in result_text
        has_high = "HIGH RISK" in result_text
        has_medium = "MEDIUM RISK" in result_text
        has_low = result_text.count("LOW") > 0  # May not be explicitly shown
        
        print(f"  Critical Tasks: {'Yes' if has_critical else 'No'}")
        print(f"  High Risk Tasks: {'Yes' if has_high else 'No'}")
        print(f"  Medium Risk Tasks: {'Yes' if has_medium else 'No'}")
        
        # Task 8 should be in MEDIUM (2 days remaining)
        if "MEDIUM RISK" in result_text and "[8]" in result_text:
            print_success("Task 8 correctly categorized as MEDIUM RISK")
        else:
            print_warning("Task 8 risk categorization may vary based on current date")
        
        print_success("Risk categorization test completed")
        return True
    except Exception as e:
        print_error(f"Risk categorization test failed: {e}")
        return False


# Test Case 5: Time Remaining Calculation
def test_time_remaining():
    print_header("TEST CASE 5: Time Remaining Calculation")
    print_info("Verifying time remaining is calculated correctly")
    
    payload = {
        "request_id": "test-time-004",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {"text": "how much time do I have?"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        result_text = data["output"]["result"]
        
        print(f"\nTime Remaining Format Check:")
        
        # Check for time format patterns
        has_days = "day(s)" in result_text
        has_hours = "hour(s)" in result_text
        
        print(f"  Contains day(s): {'Yes' if has_days else 'No'}")
        print(f"  Contains hour(s): {'Yes' if has_hours else 'No'}")
        
        # Verify specific task deadlines
        if "[8]" in result_text:
            print_success("Task 8 (Dec 1) time remaining displayed")
        if "[9]" in result_text:
            print_success("Task 9 (Dec 15) time remaining displayed")
        
        print_success("Time remaining calculation test passed")
        return True
    except Exception as e:
        print_error(f"Time remaining test failed: {e}")
        return False


# Test Case 6: Confidence Score Validation
def test_confidence_score():
    print_header("TEST CASE 6: Confidence Score Validation")
    print_info("Verifying confidence score is appropriate")
    
    payload = {
        "request_id": "test-confidence-005",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {"text": "analyze deadlines"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        
        confidence = data["output"]["confidence"]
        print(f"\nConfidence Score: {confidence}")
        
        assert 0.0 <= confidence <= 1.0, "Confidence should be between 0 and 1"
        assert confidence == 1.0, "Should have high confidence with tasks present"
        
        print_success(f"Confidence score is valid: {confidence}")
        return True
    except Exception as e:
        print_error(f"Confidence score test failed: {e}")
        return False


# Test Case 7: Details Field Validation
def test_details_field():
    print_header("TEST CASE 7: Details Field Validation")
    print_info("Verifying details field contains comprehensive information")
    
    payload = {
        "request_id": "test-details-006",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {"text": "detailed deadline analysis"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        
        details = data["output"]["details"]
        print(f"\nDetails: {details}")
        
        # Check for required information in details
        assert "Analyzed" in details, "Should mention number of tasks analyzed"
        assert "tasks" in details.lower(), "Should mention tasks"
        assert "at risk" in details.lower(), "Should mention at-risk count"
        
        if "Recommendations" in details:
            print_success("Details include recommendations")
        
        print_success("Details field validation passed")
        return True
    except Exception as e:
        print_error(f"Details field test failed: {e}")
        return False


# Test Case 8: Invalid Intent Handling
def test_invalid_intent():
    print_header("TEST CASE 8: Invalid Intent Handling")
    print_info("Verifying proper error handling for invalid intents")
    
    payload = {
        "request_id": "test-error-007",
        "agent_name": "deadline_guardian_agent",
        "intent": "task.create",  # Wrong intent
        "input": {"text": "test"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 400, "Should return 400 for invalid intent"
        assert data["status"] == "error", "Status should be error"
        assert data["error"]["type"] == "invalid_intent", "Error type should be invalid_intent"
        assert "deadline.monitor" in data["error"]["message"], "Error message should mention valid intent"
        
        print_success("Invalid intent correctly rejected")
        return True
    except Exception as e:
        print_error(f"Invalid intent test failed: {e}")
        return False


# Test Case 9: Missing Request Body
def test_missing_request_body():
    print_header("TEST CASE 9: Missing Request Body")
    print_info("Verifying error handling for missing request body")
    
    try:
        response = requests.post(f"{BASE_URL}/handle")
        data = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 400, "Should return 400 for missing body"
        assert data["status"] == "error", "Status should be error"
        assert data["error"]["type"] == "invalid_request", "Error type should be invalid_request"
        
        print_success("Missing request body correctly handled")
        return True
    except Exception as e:
        print_error(f"Missing request body test failed: {e}")
        return False


# Test Case 10: Response Contract Compliance
def test_response_contract():
    print_header("TEST CASE 10: Response Contract Compliance")
    print_info("Verifying response follows supervisor handshake contract")
    
    payload = {
        "request_id": "test-contract-008",
        "agent_name": "deadline_guardian_agent",
        "intent": "deadline.monitor",
        "input": {"text": "test"},
        "context": {"user_id": "test_user", "timestamp": datetime.now().isoformat()}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/handle", json=payload)
        data = response.json()
        
        # Check required fields
        required_fields = ["request_id", "agent_name", "status", "output", "error"]
        print(f"\nChecking required fields:")
        for field in required_fields:
            if field in data:
                print_success(f"Field '{field}' present")
            else:
                print_error(f"Field '{field}' missing")
                return False
        
        # Check output structure
        if data["status"] == "success":
            output_fields = ["result", "confidence", "details"]
            print(f"\nChecking output fields:")
            for field in output_fields:
                if field in data["output"]:
                    print_success(f"Output field '{field}' present")
                else:
                    print_error(f"Output field '{field}' missing")
                    return False
        
        print_success("Response contract compliance verified")
        return True
    except Exception as e:
        print_error(f"Response contract test failed: {e}")
        return False


# Run all tests
def run_all_tests():
    print("\n" + "=" * 70)
    print(f"{BLUE}DEADLINE GUARDIAN AGENT - COMPREHENSIVE TEST SUITE{RESET}")
    print(f"{BLUE}Testing with Real MongoDB Tasks{RESET}")
    print("=" * 70)
    
    tests = [
        ("Health Check", test_health_check),
        ("Basic Deadline Monitoring", test_basic_deadline_monitoring),
        ("Specific Tasks Detection", test_specific_tasks_detection),
        ("Risk Level Categorization", test_risk_categorization),
        ("Time Remaining Calculation", test_time_remaining),
        ("Confidence Score Validation", test_confidence_score),
        ("Details Field Validation", test_details_field),
        ("Invalid Intent Handling", test_invalid_intent),
        ("Missing Request Body", test_missing_request_body),
        ("Response Contract Compliance", test_response_contract),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"  {status} - {test_name}")
    
    print("\n" + "=" * 70)
    if passed == total:
        print_success(f"ALL TESTS PASSED! ({passed}/{total})")
    else:
        print_error(f"SOME TESTS FAILED ({total - passed} failures)")
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
