"""Unit tests for the code agent."""
import asyncio
import pytest
from config import LLMConfig
from agent import AgentState, PlanStep, PlanStatus
from tools import FileEditorTool, PythonExecutorTool, BashExecutorTool


class TestTools:
    """Test tool implementations."""

    @pytest.mark.asyncio
    async def test_file_editor_create(self, tmp_path):
        """Test file creation."""
        tool = FileEditorTool()
        test_file = tmp_path / "test.txt"

        result = await tool.execute(
            command="create",
            path=str(test_file),
            content="Hello, World!"
        )

        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "Hello, World!"

    @pytest.mark.asyncio
    async def test_file_editor_view(self, tmp_path):
        """Test file viewing."""
        tool = FileEditorTool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        result = await tool.execute(
            command="view",
            path=str(test_file)
        )

        assert result.success
        assert "Line 1" in result.output
        assert "Line 2" in result.output

    @pytest.mark.asyncio
    async def test_python_executor(self):
        """Test Python code execution."""
        tool = PythonExecutorTool()

        result = await tool.execute(
            code="print('Hello from Python')"
        )

        assert result.success
        assert "Hello from Python" in result.output

    @pytest.mark.asyncio
    async def test_python_executor_timeout(self):
        """Test Python execution timeout."""
        tool = PythonExecutorTool()

        result = await tool.execute(
            code="import time; time.sleep(10)",
            timeout=1
        )

        assert not result.success
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_bash_executor(self):
        """Test bash command execution."""
        tool = BashExecutorTool()

        result = await tool.execute(
            command="echo 'Hello from Bash'"
        )

        assert result.success
        assert "Hello from Bash" in result.output


class TestState:
    """Test agent state management."""

    def test_plan_step_creation(self):
        """Test creating a plan step."""
        step = PlanStep(
            id=1,
            description="Test step",
            tool="file_editor",
            tool_params={"command": "view", "path": "/test"}
        )

        assert step.id == 1
        assert step.status == PlanStatus.PENDING
        assert step.tool == "file_editor"

    def test_agent_state_initialization(self):
        """Test agent state initialization."""
        state = AgentState(
            user_request="Test request",
            max_iterations=10
        )

        assert state.user_request == "Test request"
        assert state.max_iterations == 10
        assert len(state.plan) == 0
        assert not state.is_complete

    def test_get_next_pending_step(self):
        """Test getting next pending step."""
        state = AgentState(user_request="Test")

        step1 = PlanStep(id=1, description="Step 1", dependencies=[])
        step2 = PlanStep(id=2, description="Step 2", dependencies=[1])
        step3 = PlanStep(id=3, description="Step 3", dependencies=[])

        state.plan = [step1, step2, step3]

        # First pending step with no dependencies
        next_step = state.get_next_pending_step()
        assert next_step.id == 1

        # Mark step 1 as completed
        state.update_step_status(1, PlanStatus.COMPLETED)
        state.completed_steps.append(1)

        # Now step 2 should be available (dependency satisfied)
        next_step = state.get_next_pending_step()
        assert next_step.id in [2, 3]

    def test_update_step_status(self):
        """Test updating step status."""
        state = AgentState(user_request="Test")
        step = PlanStep(id=1, description="Test step")
        state.plan = [step]

        state.update_step_status(1, PlanStatus.COMPLETED, result="Success")

        assert state.plan[0].status == PlanStatus.COMPLETED
        assert state.plan[0].result == "Success"
        assert 1 in state.completed_steps

    def test_todo_list_formatting(self):
        """Test todo list formatting."""
        state = AgentState(user_request="Test")

        step1 = PlanStep(id=1, description="Step 1", status=PlanStatus.COMPLETED)
        step2 = PlanStep(id=2, description="Step 2", status=PlanStatus.IN_PROGRESS)
        step3 = PlanStep(id=3, description="Step 3", status=PlanStatus.PENDING)

        state.plan = [step1, step2, step3]
        state.current_step_id = 2
        state.completed_steps = [1]

        todo_list = state.get_todo_list()

        assert "Step 1" in todo_list
        assert "Step 2" in todo_list
        assert "Step 3" in todo_list
        assert "1/3" in todo_list


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_simple_workflow(self, tmp_path):
        """Test a simple end-to-end workflow."""
        # This would require a real LLM API key
        # For now, we'll test the components individually
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
