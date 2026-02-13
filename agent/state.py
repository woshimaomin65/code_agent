"""Agent state definitions."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PlanStatus(str, Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """A single step in the plan."""

    id: int = Field(description="Step ID")
    description: str = Field(description="Step description")
    status: PlanStatus = Field(default=PlanStatus.PENDING, description="Step status")
    tool: Optional[str] = Field(default=None, description="Tool to use")
    tool_params: Optional[Dict[str, Any]] = Field(default=None, description="Tool parameters")
    result: Optional[str] = Field(default=None, description="Execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    dependencies: List[int] = Field(default_factory=list, description="Dependent step IDs")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class AgentState(BaseModel):
    """State of the agent."""

    # User input
    user_request: str = Field(description="Original user request")

    # Plan management
    plan: List[PlanStep] = Field(default_factory=list, description="List of plan steps")
    current_step_id: Optional[int] = Field(default=None, description="Current executing step ID")

    # Execution tracking
    completed_steps: List[int] = Field(default_factory=list, description="Completed step IDs")
    failed_steps: List[int] = Field(default_factory=list, description="Failed step IDs")

    # Context and memory
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    messages: List[Dict[str, str]] = Field(default_factory=list, description="Conversation history")

    # Control flags
    needs_replan: bool = Field(default=False, description="Whether replanning is needed")
    is_complete: bool = Field(default=False, description="Whether task is complete")
    max_iterations: int = Field(default=20, description="Maximum iterations")
    iteration_count: int = Field(default=0, description="Current iteration count")

    def get_current_step(self) -> Optional[PlanStep]:
        """Get current step."""
        if self.current_step_id is None:
            return None
        for step in self.plan:
            if step.id == self.current_step_id:
                return step
        return None

    def get_next_pending_step(self) -> Optional[PlanStep]:
        """Get next pending step that has all dependencies completed."""
        for step in self.plan:
            if step.status == PlanStatus.PENDING:
                # Check if all dependencies are completed
                deps_completed = all(
                    dep_id in self.completed_steps
                    for dep_id in step.dependencies
                )
                if deps_completed:
                    return step
        return None

    def get_todo_list(self) -> str:
        """Get formatted todo list."""
        lines = ["📋 Todo List:"]
        for step in self.plan:
            status_icon = {
                PlanStatus.PENDING: "⏳",
                PlanStatus.IN_PROGRESS: "🔄",
                PlanStatus.COMPLETED: "✅",
                PlanStatus.FAILED: "❌",
                PlanStatus.SKIPPED: "⏭️",
            }[step.status]

            marker = "👉 " if step.id == self.current_step_id else "   "
            lines.append(f"{marker}{status_icon} Step {step.id}: {step.description}")

        lines.append(f"\nProgress: {len(self.completed_steps)}/{len(self.plan)} steps completed")
        return "\n".join(lines)

    def update_step_status(self, step_id: int, status: PlanStatus, result: Optional[str] = None, error: Optional[str] = None):
        """Update step status."""
        for step in self.plan:
            if step.id == step_id:
                step.status = status
                if result:
                    step.result = result
                if error:
                    step.error = error

                if status == PlanStatus.COMPLETED:
                    if step_id not in self.completed_steps:
                        self.completed_steps.append(step_id)
                elif status == PlanStatus.FAILED:
                    if step_id not in self.failed_steps:
                        self.failed_steps.append(step_id)
                break

    def get_execution_summary(self, max_steps: int = 5) -> str:
        """Get a summary of recent execution results for reflection.

        Args:
            max_steps: Maximum number of recent steps to include in detail
        """
        if not self.plan:
            return "No execution history yet."

        lines = ["📊 Execution History:"]

        # Get recent steps (last max_steps)
        recent_steps = self.plan[-max_steps:] if len(self.plan) > max_steps else self.plan
        older_steps = self.plan[:-max_steps] if len(self.plan) > max_steps else []

        # Summarize older steps
        if older_steps:
            completed = sum(1 for s in older_steps if s.status == PlanStatus.COMPLETED)
            failed = sum(1 for s in older_steps if s.status == PlanStatus.FAILED)
            lines.append(f"\n[Earlier steps: {completed} completed, {failed} failed]")

        # Detail recent steps
        lines.append("\nRecent steps:")
        for step in recent_steps:
            status_icon = {
                PlanStatus.PENDING: "⏳",
                PlanStatus.IN_PROGRESS: "🔄",
                PlanStatus.COMPLETED: "✅",
                PlanStatus.FAILED: "❌",
                PlanStatus.SKIPPED: "⏭️",
            }[step.status]

            lines.append(f"\n{status_icon} Step {step.id}: {step.description}")
            lines.append(f"   Tool: {step.tool or 'none'}")

            if step.status == PlanStatus.COMPLETED and step.result:
                result_preview = step.result[:150] + "..." if len(step.result) > 150 else step.result
                lines.append(f"   ✓ Result: {result_preview}")
            elif step.status == PlanStatus.FAILED and step.error:
                lines.append(f"   ✗ Error: {step.error}")

        return "\n".join(lines)

    def compact_messages(self, max_messages: int = 10) -> None:
        """Compact message history to prevent context explosion.

        Keeps the most recent messages and summarizes older ones.

        Args:
            max_messages: Maximum number of messages to keep in detail
        """
        if len(self.messages) <= max_messages:
            return

        # Keep recent messages
        recent_messages = self.messages[-max_messages:]
        older_messages = self.messages[:-max_messages]

        # Create summary of older messages
        summary = {
            "role": "system",
            "content": f"[Summary of {len(older_messages)} earlier messages: "
                      f"Discussed initial planning and early execution steps]"
        }

        # Replace with compacted version
        self.messages = [summary] + recent_messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
