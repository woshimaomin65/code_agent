"""Executor module for executing plan steps."""
from typing import Dict, Any
from .state import AgentState, PlanStatus
from tools import FileEditorTool, PythonExecutorTool, BashExecutorTool


class Executor:
    """Executor for running plan steps."""

    def __init__(self):
        """Initialize executor with tools."""
        self.tools = {
            "file_editor": FileEditorTool(),
            "python_executor": PythonExecutorTool(),
            "bash_executor": BashExecutorTool(),
        }

    async def execute_step(self, state: AgentState) -> AgentState:
        """Execute the current step."""
        # Get next pending step
        next_step = state.get_next_pending_step()

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
                        state.update_step_status(
                            next_step.id,
                            PlanStatus.COMPLETED,
                            result=result.output
                        )
                        print(f"✅ Step {next_step.id} completed")
                        if result.output:
                            print(f"Output: {result.output[:200]}...")
                    else:
                        state.update_step_status(
                            next_step.id,
                            PlanStatus.FAILED,
                            error=result.error
                        )
                        print(f"❌ Step {next_step.id} failed: {result.error}")
                        state.needs_replan = True

                except Exception as e:
                    state.update_step_status(
                        next_step.id,
                        PlanStatus.FAILED,
                        error=str(e)
                    )
                    print(f"❌ Step {next_step.id} failed with exception: {str(e)}")
                    state.needs_replan = True

        # Increment iteration count
        state.iteration_count += 1

        # Check if max iterations reached
        if state.iteration_count >= state.max_iterations:
            state.is_complete = True
            print(f"\n⚠️ Max iterations ({state.max_iterations}) reached")

        return state
