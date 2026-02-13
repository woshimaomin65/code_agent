"""Planner module for generating execution plans."""
import json
import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState, PlanStep, PlanStatus
from config.llm_config import LLMConfig
from utils.logger import invoke_llm_with_streaming
from utils.json_extractor import JSONExtractor

def js(data):
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


class Planner:
    """Planner for generating execution plans."""

    def __init__(self, llm_config: LLMConfig):
        """Initialize planner with LLM config."""
        self.llm = ChatOpenAI(
            base_url=llm_config.api_base,
            api_key=llm_config.api_key,
            model=llm_config.model,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            **({"extra_body": llm_config.extra_body} if llm_config.extra_body else {})
        )
        self.streaming = llm_config.streaming
        self.logger = logging.getLogger("code_agent")
        self.json_extractor = JSONExtractor(self.logger)

    async def create_plan(self, state: AgentState) -> AgentState:
        """Create initial plan from user request."""
        system_prompt = """You are a planning assistant. Given a user request, create a detailed step-by-step plan.

Available tools:
1. file_editor - For file operations
   - view: View entire file or with range {"command": "view", "path": "/path", "view_range": [start, end]}
   - view_context: View file with context around a line {"command": "view_context", "path": "/path", "center_line": 50, "context_lines": 20}
   - create: Create new file {"command": "create", "path": "/path", "content": "..."}
   - str_replace: Replace string {"command": "str_replace", "path": "/path", "old_str": "...", "new_str": "..."}
   - insert: Insert at line {"command": "insert", "path": "/path", "insert_line": 10, "content": "..."}
   - delete: Delete file {"command": "delete", "path": "/path"}
2. python_executor - For executing Python code {"code": "python code"}
3. bash_executor - For executing bash commands {"command": "bash command"}

Return a JSON array of steps, each with:
- id: step number (starting from 1)
- description: what to do
- tool: which tool to use (file_editor, python_executor, bash_executor, or null for thinking steps)
- tool_params: parameters for the tool (or null)
- dependencies: list of step IDs that must complete first (or empty list)

Example:
[
  {
    "id": 1,
    "description": "View the current directory structure",
    "tool": "bash_executor",
    "tool_params": {"command": "ls -la"},
    "dependencies": []
  },
  {
    "id": 2,
    "description": "Create a new Python file",
    "tool": "file_editor",
    "tool_params": {"command": "create", "path": "/path/to/file.py", "content": "print('hello')"},
    "dependencies": [1]
  }
]

IMPORTANT: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON array. Ensure proper JSON formatting with correct commas and no trailing commas."""

        user_prompt = f"User request: {state.user_request}\n\nCreate a detailed execution plan."

        max_retries = 3
        for attempt in range(max_retries):
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                # Use streaming utility with think tag handling
                _, response_content = await invoke_llm_with_streaming(
                    self.llm,
                    messages,
                    streaming=self.streaming,
                    module="planner",
                    logger=self.logger
                )

                plan_json = self._extract_json(response_content)

                # Parse plan steps with error handling
                plan_steps = []
                for step_data in plan_json:
                    try:
                        step = PlanStep(
                            id=step_data["id"],
                            description=step_data["description"],
                            status=PlanStatus.PENDING,
                            tool=step_data.get("tool"),
                            tool_params=step_data.get("tool_params"),
                            dependencies=step_data.get("dependencies", [])
                        )
                        plan_steps.append(step)
                    except KeyError as e:
                        self.logger.error(f"Missing required field in step: {e}")
                        raise ValueError(f"Invalid step structure: missing field {e}")

                state.plan = plan_steps
                state.messages.append({
                    "role": "assistant",
                    "content": f"Created plan with {len(plan_steps)} steps"
                })

                return state

            except (ValueError, json.JSONDecodeError) as e:
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    # Add feedback to retry prompt
                    user_prompt = f"{user_prompt}\n\nPrevious attempt failed with error: {e}\nPlease ensure you return valid JSON with proper formatting."
                else:
                    # Final attempt failed
                    error_msg = f"Failed to create plan after {max_retries} attempts: {e}"
                    self.logger.error(error_msg)
                    state.messages.append({
                        "role": "assistant",
                        "content": f"Error: {error_msg}"
                    })
                    raise ValueError(error_msg)

    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON array from LLM response using shared utility."""
        result = self.json_extractor.extract(text, expect_array=True)

        # Additional validation for plan-specific requirements
        if not self._validate_plan_json(result):
            raise ValueError("JSON does not match expected plan structure")

        return result

    def _validate_plan_json(self, plan_data: List[Dict[str, Any]]) -> bool:
        """Validate that the parsed JSON has the expected plan structure."""
        if not isinstance(plan_data, list) or len(plan_data) == 0:
            return False

        # Check that each step has required fields
        required_fields = ['id', 'description']
        for step in plan_data:
            if not isinstance(step, dict):
                return False
            for field in required_fields:
                if field not in step:
                    return False

        return True
