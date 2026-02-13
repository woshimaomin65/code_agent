# JSON Parsing Robustness Improvements

## Problem
The planner was failing with `json.decoder.JSONDecodeError` when the LLM generated malformed JSON (e.g., missing commas, trailing commas, etc.). This caused the entire agent to crash.

## Solution
Implemented comprehensive robustness improvements for JSON parsing across all modules:

### 1. Created Shared JSON Extraction Utility
**File**: `utils/json_extractor.py`

Features:
- Multiple extraction strategies (basic, code block, with repair)
- Automatic JSON repair for common issues:
  - Trailing commas before `]` or `}`
  - Missing commas between objects
  - Comments (`//` and `/* */`)
- Validation of extracted JSON structure
- Detailed error logging for debugging

### 2. Updated Planner Module
**File**: `agent/planner.py`

Improvements:
- Uses shared `JSONExtractor` utility
- Retry logic (up to 3 attempts) with feedback to LLM
- Better error handling with specific exception catching
- Validates plan structure before accepting
- Improved system prompt with explicit JSON formatting instructions

### 3. Updated Replanner Module
**File**: `agent/replanner.py`

Improvements:
- Uses shared `JSONExtractor` utility for both local fix and full replan
- Handles both JSON objects (local fix) and arrays (full replan)
- Maintains existing fallback strategies
- Cleaned up unused imports

### 4. Updated Executor Module
**File**: `agent/executor.py`

Improvements:
- Uses shared `JSONExtractor` utility for goal verification
- Better error handling with graceful fallback
- Maintains existing verification logic

### 5. Added Tests
**File**: `test/test_json_extractor.py`

Test coverage:
- Basic array and object extraction
- Code block extraction (markdown)
- Trailing comma repair
- JSON surrounded by text
- Error handling for invalid JSON

## Benefits
1. **Robustness**: Handles malformed JSON from LLM responses
2. **Maintainability**: Centralized JSON extraction logic
3. **Debugging**: Better error messages and logging
4. **Reliability**: Retry logic prevents single failures from crashing the agent
5. **Flexibility**: Multiple extraction strategies increase success rate

## Testing
All tests pass successfully:
```bash
PYTHONPATH=/Users/maomin/programs/vscode/code_agent python test/test_json_extractor.py
✅ All tests passed!
```
