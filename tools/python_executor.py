"""Python code executor tool."""
import sys
import multiprocessing
from io import StringIO
from typing import Optional
from .base import BaseTool, ToolResult


class PythonExecutorTool(BaseTool):
    """Tool for executing Python code."""

    def __init__(self):
        self.name = "python_executor"
        self.description = "Execute Python code and return output. Only print outputs are captured."
        self.parameters = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30
                }
            },
            "required": ["code"]
        }

    def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
        """Run code in isolated process."""
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            exec(code, safe_globals, safe_globals)
            result_dict["output"] = output_buffer.getvalue()
            result_dict["success"] = True
        except Exception as e:
            result_dict["output"] = ""
            result_dict["error"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        code: str,
        timeout: int = 30,
        **kwargs
    ) -> ToolResult:
        """Execute Python code with timeout."""
        try:
            with multiprocessing.Manager() as manager:
                result = manager.dict({"output": "", "error": None, "success": False})

                if isinstance(__builtins__, dict):
                    safe_globals = {"__builtins__": __builtins__}
                else:
                    safe_globals = {"__builtins__": __builtins__.__dict__.copy()}

                proc = multiprocessing.Process(
                    target=self._run_code,
                    args=(code, result, safe_globals)
                )
                proc.start()
                proc.join(timeout)

                if proc.is_alive():
                    proc.terminate()
                    proc.join(1)
                    return ToolResult(
                        success=False,
                        error=f"Execution timeout after {timeout} seconds"
                    )

                return ToolResult(
                    success=result["success"],
                    output=result["output"],
                    error=result.get("error")
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
