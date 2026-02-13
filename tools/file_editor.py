"""File editor tool for file operations."""
import os
import shutil
from pathlib import Path
from typing import Literal, Optional
from .base import BaseTool, ToolResult


class FileEditorTool(BaseTool):
    """Tool for file and directory operations."""

    def __init__(self):
        self.name = "file_editor"
        self.description = """File editor tool for viewing, creating, editing, copying, and deleting files.
Commands:
- view: View file or directory contents
- create: Create a new file with content
- copy: Copy file or directory
- delete: Delete file or directory
- str_replace: Replace string in file
- insert: Insert content at specific line
"""
        self.parameters = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "copy", "delete", "str_replace", "insert"],
                    "description": "Command to execute"
                },
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                },
                "content": {
                    "type": "string",
                    "description": "Content for create command"
                },
                "target_path": {
                    "type": "string",
                    "description": "Target path for copy command"
                },
                "old_str": {
                    "type": "string",
                    "description": "String to replace in str_replace command"
                },
                "new_str": {
                    "type": "string",
                    "description": "New string for str_replace command"
                },
                "insert_line": {
                    "type": "integer",
                    "description": "Line number to insert at (for insert command)"
                },
                "view_range": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Line range for view command [start, end]"
                }
            },
            "required": ["command", "path"]
        }

    async def execute(
        self,
        command: Literal["view", "create", "copy", "delete", "str_replace", "insert"],
        path: str,
        content: Optional[str] = None,
        target_path: Optional[str] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
        view_range: Optional[list] = None,
        **kwargs
    ) -> ToolResult:
        """Execute file operation command."""
        try:
            if command == "view":
                return await self._view(path, view_range)
            elif command == "create":
                return await self._create(path, content)
            elif command == "copy":
                return await self._copy(path, target_path)
            elif command == "delete":
                return await self._delete(path)
            elif command == "str_replace":
                return await self._str_replace(path, old_str, new_str)
            elif command == "insert":
                return await self._insert(path, insert_line, content)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown command: {command}"
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _view(self, path: str, view_range: Optional[list] = None) -> ToolResult:
        """View file or directory contents."""
        p = Path(path)
        if not p.exists():
            return ToolResult(success=False, error=f"Path does not exist: {path}")

        if p.is_dir():
            items = list(p.iterdir())
            output = f"Directory: {path}\n"
            output += "\n".join([f"  {item.name}" for item in items])
            return ToolResult(success=True, output=output)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if view_range:
                start, end = view_range
                lines = lines[start-1:end] if end != -1 else lines[start-1:]

            numbered_lines = [f"{i+1:6}\t{line.rstrip()}" for i, line in enumerate(lines)]
            output = "\n".join(numbered_lines)
            return ToolResult(success=True, output=output)

    async def _create(self, path: str, content: Optional[str]) -> ToolResult:
        """Create a new file."""
        p = Path(path)
        if p.exists():
            return ToolResult(success=False, error=f"File already exists: {path}")

        p.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content or "")

        return ToolResult(success=True, output=f"File created: {path}")

    async def _copy(self, src_path: str, target_path: Optional[str]) -> ToolResult:
        """Copy file or directory."""
        if not target_path:
            return ToolResult(success=False, error="target_path is required")

        src = Path(src_path)
        dst = Path(target_path)

        if not src.exists():
            return ToolResult(success=False, error=f"Source does not exist: {src_path}")

        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        return ToolResult(success=True, output=f"Copied from {src_path} to {target_path}")

    async def _delete(self, path: str) -> ToolResult:
        """Delete file or directory."""
        p = Path(path)
        if not p.exists():
            return ToolResult(success=False, error=f"Path does not exist: {path}")

        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

        return ToolResult(success=True, output=f"Deleted: {path}")

    async def _str_replace(
        self,
        path: str,
        old_str: Optional[str],
        new_str: Optional[str]
    ) -> ToolResult:
        """Replace string in file."""
        if not old_str:
            return ToolResult(success=False, error="old_str is required")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_str not in content:
            return ToolResult(success=False, error=f"String not found: {old_str}")

        count = content.count(old_str)
        if count > 1:
            return ToolResult(
                success=False,
                error=f"String appears {count} times, must be unique"
            )

        new_content = content.replace(old_str, new_str or "")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return ToolResult(success=True, output=f"Replaced in {path}")

    async def _insert(
        self,
        path: str,
        insert_line: Optional[int],
        content: Optional[str]
    ) -> ToolResult:
        """Insert content at specific line."""
        if insert_line is None:
            return ToolResult(success=False, error="insert_line is required")
        if not content:
            return ToolResult(success=False, error="content is required")

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        lines.insert(insert_line, content + '\n')

        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return ToolResult(success=True, output=f"Inserted at line {insert_line} in {path}")

