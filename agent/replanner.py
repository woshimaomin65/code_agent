"""Replanner module for adjusting plans based on execution results."""
import json
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState, PlanStep, PlanStatus
from config.llm_config import LLMConfig


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
        )

    async def replan(self, state: AgentState) -> AgentState:
        """Replan based on current state and failures."""
        # Get failed steps
        failed_steps = [step for step in state.plan if step.status == PlanStatus.FAILED]

        if not failed_steps:
            state.needs_replan = False
            return state

        system_prompt = """You are a replanning assistant. Given a failed execution step, adjust the plan.

You can:
1. Modify the failed step with corrected parameters
2. Add new steps before or after the failed step
3. Skip the failed step if it's not critical
4. Add alternative approaches

Return a JSON object with:
- action: "modify", "add_steps", "skip", or "alternative"
- steps: array of new/modified steps (same format as original plan)

Available tools:
1. file_editor - For file operations (view, create, copy, delete, str_replace, insert)
2. python_executor - For executing Python code
3. bash_executor - For executing bash commands"""

        # Build context
        context = f"""Original request: {state.user_request}

Current plan status:
{state.get_todo_list()}

Failed steps:
"""
        for step in failed_steps:
            context += f"\nStep {step.id}: {step.description}"
            context += f"\nTool: {step.tool}"
            context += f"\nParams: {step.tool_params}"
            context += f"\nError: {step.error}\n"

        context += "\n\nProvide a replanning strategy to handle these failures."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]

        response = await self.llm.ainvoke(messages)
        replan_data = self._extract_json(response.content)

        action = replan_data.get("action", "modify")
        new_steps = replan_data.get("steps", [])

        if action == "skip":
            # Skip failed steps
            for step in failed_steps:
                state.update_step_status(step.id, PlanStatus.SKIPPED)
            print(f"⏭️ Skipped {len(failed_steps)} failed steps")

        elif action == "modify":
            # Modify failed steps
            for new_step_data in new_steps:
                step_id = new_step_data["id"]
                for step in state.plan:
                    if step.id == step_id:
                        step.description = new_step_data.get("description", step.description)
                        step.tool = new_step_data.get("tool", step.tool)
                        step.tool_params = new_step_data.get("tool_params", step.tool_params)
                        step.status = PlanStatus.PENDING
                        step.error = None
                        # Remove from failed steps
                        if step_id in state.failed_steps:
                            state.failed_steps.remove(step_id)
                        print(f"🔄 Modified Step {step_id}")
                        break

        elif action == "add_steps":
            # Add new steps
            max_id = max([s.id for s in state.plan]) if state.plan else 0
            for i, new_step_data in enumerate(new_steps):
                new_step = PlanStep(
                    id=max_id + i + 1,
                    description=new_step_data["description"],
                    status=PlanStatus.PENDING,
                    tool=new_step_data.get("tool"),
                    tool_params=new_step_data.get("tool_params"),
                    dependencies=new_step_data.get("dependencies", [])
                )
                state.plan.append(new_step)
                print(f"➕ Added Step {new_step.id}: {new_step.description}")

        elif action == "alternative":
            # Replace failed steps with alternatives
            for step in failed_steps:
                state.update_step_status(step.id, PlanStatus.SKIPPED)

            max_id = max([s.id for s in state.plan]) if state.plan else 0
            for i, new_step_data in enumerate(new_steps):
                new_step = PlanStep(
                    id=max_id + i + 1,
                    description=new_step_data["description"],
                    status=PlanStatus.PENDING,
                    tool=new_step_data.get("tool"),
                    tool_params=new_step_data.get("tool_params"),
                    dependencies=new_step_data.get("dependencies", [])
                )
                state.plan.append(new_step)
                print(f"🔀 Alternative Step {new_step.id}: {new_step.description}")

        state.needs_replan = False
        return state

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try to find JSON object in the response
        start = text.find('{')
        end = text.rfind('}') + 1

        if start == -1 or end == 0:
            # Fallback: return default action
            return {"action": "skip", "steps": []}

        json_str = text[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"action": "skip", "steps": []}
