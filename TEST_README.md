# Test Runner Script for Deadline Guardian Agent

## Quick Start

Run all tests:
```bash
python test_complete.py
```

Or use pytest:
```bash
pytest test_complete.py -v
```

## Test Coverage

Run with coverage report:
```bash
pytest test_complete.py --cov=app --cov-report=html
```

## Individual Test Suites

Run specific test class:
```bash
pytest test_complete.py::TestRiskCalculation -v
pytest test_complete.py::TestDependencyGraph -v
pytest test_complete.py::TestAPIEndpoints -v
```

## Test Categories

### 1. **Unit Tests**
- `TestRiskCalculation` - Risk level calculation logic
- `TestTimeFormatting` - Time remaining formatting
- `TestDependencyGraph` - Dependency graph construction
- `TestCascadingRisks` - Cascading risk analysis

### 2. **Integration Tests**
- `TestAPIEndpoints` - Flask API endpoint testing
- `TestFullIntegration` - Complete workflow testing

### 3. **AI Tests**
- `TestAIIntegration` - AI analysis with mocked LLM

### 4. **Edge Cases**
- `TestEdgeCases` - Error handling and edge cases

## Test Data

All tests use mocked data and don't require:
- MongoDB connection
- OpenRouter API key
- External services

## Expected Results

All tests should pass with:
- ✅ Risk calculation working correctly
- ✅ Dependency graph building properly
- ✅ API endpoints responding correctly
- ✅ AI integration handling mocks
- ✅ Edge cases handled gracefully

## Troubleshooting

If tests fail:
1. Ensure `app.py` is in the same directory
2. Check Python version (3.8+ required)
3. Install dependencies: `pip install -r requirements.txt`
4. Verify Flask app structure matches test expectations
