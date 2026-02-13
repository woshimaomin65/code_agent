"""Bash command executor tool."""
import asyncio
import subprocess
from typing import Optional
from .base import BaseTool, ToolResult


class BashExecutorTool(BaseTool):
    """Tool for executing bash commands."""

    def __init__(self):
        self.name = "bash_executor"
        self.description = "Execute bash commands and return output."
        self.parameters = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Bash command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30
                }
            },
            "required": ["command"]
        }

    async def execute(
        self,
        command: str,
        timeout: int = 30,
        **kwargs
    ) -> ToolResult:
        """Execute bash command with timeout."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timeout after {timeout} seconds"
                )

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=stdout.decode('utf-8')
                )
            else:
                return ToolResult(
                    success=False,
                    output=stdout.decode('utf-8'),
                    error=stderr.decode('utf-8')
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
