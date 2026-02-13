"""Base tool class and result types."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = Field(description="Whether execution was successful")
    output: str = Field(default="", description="Output from the tool")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"


class BaseTool(ABC):
    """Base class for all tools."""

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
