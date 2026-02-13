"""Replanner module for adjusting plans based on execution results."""
import json
import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState, PlanStep, PlanStatus
from config.llm_config import LLMConfig
from utils.logger import invoke_llm_with_streaming


class Replanner:
    """Replanner for adjusting execution plans."""

    def __init__(self, llm_config: LLMConfig):
        """Initialize replanner with LLM config."""
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

    async def replan(self, state: AgentState) -> AgentState:
        """Replan from the first failed step onwards, regenerating all remaining steps."""
        # Get failed steps
        failed_steps = [step for step in state.plan if step.status == PlanStatus.FAILED]

        if not failed_steps:
            state.needs_replan = False
            return state

        # Find the first failed step
        first_failed_step = min(failed_steps, key=lambda s: s.id)

        # Get completed steps (keep these as-is)
        completed_steps = [step for step in state.plan if step.status == PlanStatus.COMPLETED and step.id < first_failed_step.id]

        system_prompt = """You are a replanning assistant. Given a failed execution and execution history, regenerate the plan from the failure point onwards.

Your task:
1. Analyze what went wrong and why
2. Learn from the execution history to avoid repeating mistakes
3. Generate a NEW complete plan starting from the failed step
4. Consider what has already been completed successfully

Return a JSON array of steps (starting from the failed step onwards):
[
  {
    "id": <step_number>,
    "description": "what to do",
    "tool": "tool_name",
    "tool_params": {"param": "value"},
    "dependencies": []
  },
  ...
]

Available tools:
1. file_editor - For file operations
   - view: View entire file or with range {"command": "view", "path": "/path", "view_range": [start, end]}
   - view_context: View file with context around a line {"command": "view_context", "path": "/path", "center_line": 50, "context_lines": 20}
   - create: Create new file {"command": "create", "path": "/path", "content": "..."}
   - str_replace: Replace string {"command": "str_replace", "path": "/path", "old_str": "...", "new_str": "..."}
   - insert: Insert at line {"command": "insert", "path": "/path", "insert_line": 10, "content": "..."}
   - delete: Delete file {"command": "delete", "path": "/path"}

2. python_executor - For executing Python code
   - {"code": "python code to execute"}

3. bash_executor - For executing bash commands
   - {"command": "bash command"}

CRITICAL:
- For file_editor insert command, you MUST provide "insert_line" parameter (line number where to insert)
- Analyze the error message carefully to understand what went wrong
- Don't repeat the same mistake that caused the failure"""

        # Build comprehensive context
        context = f"""Original request: {state.user_request}

=== EXECUTION HISTORY ===
{state.get_execution_summary(max_steps=15)}

=== COMPLETED STEPS (Keep these, don't regenerate) ===
"""
        for step in completed_steps:
            context += f"✅ Step {step.id}: {step.description}\n"

        context += f"""
=== FAILED STEP (Start regenerating from here) ===
Step {first_failed_step.id}: {first_failed_step.description}
Tool: {first_failed_step.tool}
Parameters: {first_failed_step.tool_params}
Error: {first_failed_step.error}
"""
        if first_failed_step.result:
            context += f"Partial output: {first_failed_step.result[:1000]}\n"

        # Include other failed/pending steps for context
        remaining_steps = [s for s in state.plan if s.id > first_failed_step.id]
        if remaining_steps:
            context += f"\n=== ORIGINAL REMAINING STEPS (for reference, will be replaced) ===\n"
            for step in remaining_steps[:5]:  # Show first 5 for context
                context += f"Step {step.id}: {step.description}\n"

        context += f"""
=== YOUR TASK ===
Regenerate the plan starting from Step {first_failed_step.id} onwards.
- Fix the error that caused Step {first_failed_step.id} to fail
- Continue with the remaining steps needed to complete the original request
- Learn from the execution history to avoid repeating mistakes
- Ensure all tool parameters are correct and complete

Return a JSON array of steps starting from Step {first_failed_step.id}."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]

        # Use streaming utility with think tag handling
        _, response_content = await invoke_llm_with_streaming(
            self.llm,
            messages,
            streaming=self.streaming,
            module="replanner",
            logger=self.logger
        )

        try:
            new_steps_data = self._extract_json_array(response_content)

            # Remove all steps from the first failed step onwards
            state.plan = [s for s in state.plan if s.id < first_failed_step.id]

            # Add the new regenerated steps
            for step_data in new_steps_data:
                new_step = PlanStep(
                    id=step_data["id"],
                    description=step_data["description"],
                    status=PlanStatus.PENDING,
                    tool=step_data.get("tool"),
                    tool_params=step_data.get("tool_params"),
                    dependencies=step_data.get("dependencies", [])
                )
                state.plan.append(new_step)
                print(f"🔄 Regenerated Step {new_step.id}: {new_step.description}")

            # Clear failed steps tracking
            state.failed_steps = []

            print(f"\n✨ Replanned from Step {first_failed_step.id} onwards ({len(new_steps_data)} steps)")

        except Exception as e:
            self.logger.error(f"Failed to parse replan response: {str(e)}")
            # Fallback: just reset the failed step to pending
            first_failed_step.status = PlanStatus.PENDING
            first_failed_step.error = None
            print(f"⚠️ Replan parsing failed, retrying failed step as-is")

        state.needs_replan = False
        return state

    def _extract_json_array(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON array from LLM response."""
        # Try to find JSON array in the response
        start = text.find('[')
        end = text.rfind(']') + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")

        json_str = text[start:end]
        return json.loads(json_str)
