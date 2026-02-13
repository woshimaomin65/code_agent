"""Executor module for executing plan steps."""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState, PlanStatus
from tools import FileEditorTool, PythonExecutorTool, BashExecutorTool
from config.llm_config import LLMConfig
from utils.logger import invoke_llm_with_streaming


class Executor:
    """Executor for running plan steps."""

    def __init__(self, llm_config: LLMConfig = None):
        """Initialize executor with tools."""
        self.tools = {
            "file_editor": FileEditorTool(),
            "python_executor": PythonExecutorTool(),
            "bash_executor": BashExecutorTool(),
        }
        self.llm = None
        self.streaming = False
        self.logger = logging.getLogger("code_agent")
        if llm_config:
            self.llm = ChatOpenAI(
                base_url=llm_config.api_base,
                api_key=llm_config.api_key,
                model=llm_config.model,
                temperature=0.3,  # Lower temperature for verification
                max_tokens=500,
                **({"extra_body": llm_config.extra_body} if llm_config.extra_body else {})
            )
            self.streaming = llm_config.streaming

    async def _verify_goal_achievement(
        self,
        step_description: str,
        tool_name: str,
        tool_params: Dict[str, Any],
        execution_output: str
    ) -> tuple[bool, str]:
        """Verify if the execution result achieved the step's goal.

        Returns:
            (is_achieved, reason)
        """
        if not self.llm:
            # No LLM available, trust the tool's success flag
            return True, "No verification LLM available"

        system_prompt = """You are a verification assistant. Your job is to determine if an execution result actually achieved the intended goal.

Analyze:
1. What was the goal (from the step description)?
2. What tool was used and with what parameters?
3. What was the actual output?
4. Did the output indicate the goal was achieved?

Respond with a JSON object:
{
  "achieved": true/false,
  "confidence": "high"/"medium"/"low",
  "reason": "brief explanation"
}

Examples of NOT achieved:
- Goal: "Create file with content X", Output: "File created" (no confirmation of content)
- Goal: "Replace string A with B", Output: "String not found"
- Goal: "Run tests", Output: "2 tests failed"

Examples of achieved:
- Goal: "Create file test.py", Output: "File created: test.py"
- Goal: "List files", Output: "file1.txt\nfile2.txt" (shows files)
- Goal: "Delete file", Output: "Deleted: test.txt"
"""

        user_prompt = f"""Step goal: {step_description}

Tool used: {tool_name}
Tool parameters: {tool_params}

Execution output:
{execution_output[:5000] if execution_output else "No output"}

Did this execution achieve the goal?"""

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
                module="goal_verifier",
                logger=self.logger
            )

            # Parse response
            import json
            start = response_content.find('{')
            end = response_content.rfind('}') + 1

            if start != -1 and end > start:
                result = json.loads(response_content[start:end])
                achieved = result.get("achieved", True)
                reason = result.get("reason", "Verification completed")
                confidence = result.get("confidence", "medium")

                # If low confidence, treat as achieved to avoid false negatives
                if confidence == "low":
                    return True, f"Low confidence: {reason}"

                return achieved, reason
            else:
                # Failed to parse, assume achieved
                return True, "Failed to parse verification response"

        except Exception as e:
            self.logger.warning(f"Goal verification failed: {str(e)}")
            # On error, assume achieved to avoid blocking progress
            return True, f"Verification error: {str(e)}"

    async def execute_step(self, state: AgentState) -> AgentState:
        """Execute the current step."""
        # Get next pending step
        next_step = state.get_next_pending_step()
        #debug  打印当前执行的结果和状态
        print('-'*50)
        print(state.get_execution_summary(max_steps=20))
        print('-'*50)

        if next_step is None:
            # No more steps to execute
            state.is_complete = True
            return state

        # Mark step as in progress
        state.current_step_id = next_step.id
        state.update_step_status(next_step.id, PlanStatus.IN_PROGRESS)

        print(f"\n🔄 Executing Step {next_step.id}: {next_step.description}")

        # Execute the step
        if next_step.tool is None:
            # Thinking step, just mark as completed
            state.update_step_status(
                next_step.id,
                PlanStatus.COMPLETED,
                result="Thinking step completed"
            )
        else:
            # Execute tool
            tool = self.tools.get(next_step.tool)
            if tool is None:
                state.update_step_status(
                    next_step.id,
                    PlanStatus.FAILED,
                    error=f"Unknown tool: {next_step.tool}"
                )
                state.needs_replan = True
            else:
                try:
                    result = await tool.execute(**(next_step.tool_params or {}))

                    if result.success:
                        # Verify if the goal was actually achieved
                        goal_achieved, verification_reason = await self._verify_goal_achievement(
                            step_description=next_step.description,
                            tool_name=next_step.tool,
                            tool_params=next_step.tool_params or {},
                            execution_output=result.output or ""
                        )

                        if goal_achieved:
                            state.update_step_status(
                                next_step.id,
                                PlanStatus.COMPLETED,
                                result=result.output
                            )
                            print(f"✅ Step {next_step.id} completed")
                            if result.output:
                                print(f"Output: {result.output[:2000]}...")
                            print(f"✓ Verification: {verification_reason}")

                            # Add success to message history for context
                            state.messages.append({
                                "role": "assistant",
                                "content": f"Step {next_step.id} completed: {next_step.description}\nOutput: {result.output[:300] if result.output else 'No output'}\nVerification: {verification_reason}"
                            })
                        else:
                            # Tool succeeded but goal not achieved
                            state.update_step_status(
                                next_step.id,
                                PlanStatus.FAILED,
                                error=f"Goal not achieved: {verification_reason}"
                            )
                            print(f"⚠️ Step {next_step.id} tool succeeded but goal not achieved")
                            print(f"Reason: {verification_reason}")
                            state.needs_replan = True

                            # Add to message history
                            state.messages.append({
                                "role": "assistant",
                                "content": f"Step {next_step.id} goal not achieved: {next_step.description}\nTool output: {result.output[:2000] if result.output else 'No output'}\nVerification failed: {verification_reason}"
                            })
                    else:
                        # Tool execution failed
                        state.update_step_status(
                            next_step.id,
                            PlanStatus.FAILED,
                            error=result.error
                        )
                        print(f"❌ Step {next_step.id} failed: {result.error}")
                        state.needs_replan = True

                        # Add failure to message history for reflection
                        state.messages.append({
                            "role": "assistant",
                            "content": f"Step {next_step.id} failed: {next_step.description}\nError: {result.error}\nTool: {next_step.tool}\nParams: {next_step.tool_params}"
                        })

                except Exception as e:
                    state.update_step_status(
                        next_step.id,
                        PlanStatus.FAILED,
                        error=str(e)
                    )
                    print(f"❌ Step {next_step.id} failed with exception: {str(e)}")
                    state.needs_replan = True

                    # Add exception to message history for reflection
                    state.messages.append({
                        "role": "assistant",
                        "content": f"Step {next_step.id} exception: {next_step.description}\nException: {str(e)}\nTool: {next_step.tool}\nParams: {next_step.tool_params}"
                    })

        # Increment iteration count
        state.iteration_count += 1

        # Compact message history to prevent context explosion
        # Keep last 15 messages to maintain recent context
        state.compact_messages(max_messages=15)

        # Check if max iterations reached
        if state.iteration_count >= state.max_iterations:
            state.is_complete = True
            print(f"\n⚠️ Max iterations ({state.max_iterations}) reached")

        return state
