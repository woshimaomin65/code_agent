# Code Agent

A LangGraph-based code agent with dynamic plan management, state machine control, and extensible tool system.

## Features

- 🎯 **Plan and Execute**: Intelligent planning with step-by-step execution
- 🔄 **Dynamic Replanning**: Automatically adjusts plan when steps fail
- 📋 **Todo List Tracking**: Visual progress tracking with status indicators
- 🛠️ **Extensible Tools**: File operations, Python execution, and bash commands
- 🤖 **LLM-Powered**: Uses DeepSeek or any OpenAI-compatible API

## Architecture

```
code_agent/
├── config/          # LLM configuration
├── tools/           # Tool implementations
│   ├── file_editor.py      # File operations
│   ├── python_executor.py  # Python code execution
│   └── bash_executor.py    # Bash command execution
├── agent/           # Core agent logic
│   ├── state.py            # State management
│   ├── planner.py          # Plan generation
│   ├── executor.py         # Step execution
│   ├── replanner.py        # Dynamic replanning
│   └── graph.py            # LangGraph workflow
├── utils/           # Utilities
└── main.py          # Entry point
```

## Installation

```bash
cd /Users/maomin/programs/vscode/code_agent
pip install -r requirements.txt
```

## Configuration

The LLM configuration is set in `main.py`:

```python
llm_config = LLMConfig(
    api_base="https://api.deepseek.com",
    api_key="your-api-key",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=4096
)
```

## Usage

Run the agent:

```bash
python main.py
```

Example requests:
- "Create a Python script that calculates fibonacci numbers"
- "Copy all .py files from src/ to backup/"
- "Write a script to analyze log files and generate a report"

## State Machine

The agent uses a state machine with the following flow:

```
Plan → Execute → [Replan if needed] → Execute → ... → End
```

### Plan States

- ⏳ **PENDING**: Step not yet started
- 🔄 **IN_PROGRESS**: Currently executing
- ✅ **COMPLETED**: Successfully completed
- ❌ **FAILED**: Execution failed
- ⏭️ **SKIPPED**: Skipped due to replanning

## Tools

### File Editor
- `view`: View file/directory contents
- `create`: Create new files
- `copy`: Copy files/directories
- `delete`: Delete files/directories
- `str_replace`: Replace strings in files
- `insert`: Insert content at specific lines

### Python Executor
- Execute Python code with timeout
- Captures print outputs
- Safe execution environment

### Bash Executor
- Execute bash commands
- Timeout control
- Captures stdout/stderr

## Extending

### Adding New Tools

1. Create a new tool class in `tools/`:

```python
from .base import BaseTool, ToolResult

class MyTool(BaseTool):
    def __init__(self):
        self.name = "my_tool"
        self.description = "Tool description"
        self.parameters = {...}

    async def execute(self, **kwargs) -> ToolResult:
        # Implementation
        pass
```

2. Register in `agent/executor.py`:

```python
self.tools = {
    "my_tool": MyTool(),
    ...
}
```

### Customizing State

Modify `agent/state.py` to add new state fields or methods.

### Adjusting Workflow

Edit `agent/graph.py` to change the execution flow or add new nodes.

## Examples

### Example 1: File Operations

Request: "Create a Python file that prints hello world"

Plan:
1. Create file with Python code
2. Execute the file to verify

### Example 2: Code Analysis

Request: "Analyze all Python files in the current directory"

Plan:
1. List all .py files
2. Read each file
3. Generate analysis report

## License

MIT
