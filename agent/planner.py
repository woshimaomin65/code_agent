"""Planner module for generating execution plans."""
import json
import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState, PlanStep, PlanStatus
from config.llm_config import LLMConfig
from utils.logger import log_llm_interaction


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
        )
        self.logger = logging.getLogger("code_agent")

    async def create_plan(self, state: AgentState) -> AgentState:
        """Create initial plan from user request."""
        system_prompt = """You are a planning assistant. Given a user request, create a detailed step-by-step plan.

Available tools:
1. file_editor - For file operations (view, create, copy, delete, str_replace, insert)
2. python_executor - For executing Python code
3. bash_executor - For executing bash commands

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

Be specific and break down complex tasks into smaller steps."""

        user_prompt = f"User request: {state.user_request}\n\nCreate a detailed execution plan."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)

        # Log LLM interaction
        log_llm_interaction(
            self.logger,
            "planner",
            messages,
            response.content
        )

        plan_json = self._extract_json(response.content)

        # Parse plan steps
        plan_steps = []
        for step_data in plan_json:
            step = PlanStep(
                id=step_data["id"],
                description=step_data["description"],
                status=PlanStatus.PENDING,
                tool=step_data.get("tool"),
                tool_params=step_data.get("tool_params"),
                dependencies=step_data.get("dependencies", [])
            )
            plan_steps.append(step)

        state.plan = plan_steps
        state.messages.append({
            "role": "assistant",
            "content": f"Created plan with {len(plan_steps)} steps"
        })

        return state

    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        # Try to find JSON array in the response
        start = text.find('[')
        end = text.rfind(']') + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")

        json_str = text[start:end]
        return json.loads(json_str)
