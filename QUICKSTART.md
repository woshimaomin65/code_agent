# Quick Start Guide

## Installation

1. Navigate to the project directory:
```bash
cd /Users/maomin/programs/vscode/code_agent
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Basic Usage

### Method 1: Interactive Mode

Run the main script and enter your request:

```bash
python main.py
```

Example requests:
- "Create a Python file that prints hello world"
- "List all files in the current directory"
- "Write a script to calculate factorial and execute it"

### Method 2: Example Script

Run the example script with predefined tasks:

```bash
python example.py
```

### Method 3: Programmatic Usage

```python
import asyncio
from config import LLMConfig
from agent import AgentState, create_agent_graph

async def run_task():
    # Configure LLM
    llm_config = LLMConfig(
        api_base="https://api.deepseek.com",
        api_key="your-api-key",
        model="deepseek-chat"
    )

    # Create agent
    agent = create_agent_graph(llm_config)

    # Initialize state
    state = AgentState(
        user_request="Your task here",
        max_iterations=20
    )

    # Run
    result = await agent.ainvoke(state)
    print(result.get_todo_list())

asyncio.run(run_task())
```

## Configuration

### Using Environment Variables

1. Copy the example env file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```
LLM_API_KEY=your-actual-api-key
```

3. Load in your code:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("LLM_API_KEY")
```

### Direct Configuration

Edit `main.py` or `example.py`:

```python
llm_config = LLMConfig(
    api_base="https://api.deepseek.com",
    api_key="sk-your-key",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=4096
)
```

## Understanding the Output

### Todo List Format

```
📋 Todo List:
   ⏳ Step 1: View current directory
👉 🔄 Step 2: Create Python file
   ⏳ Step 3: Execute the file

Progress: 1/3 steps completed
```

Icons:
- ⏳ Pending
- 🔄 In Progress
- ✅ Completed
- ❌ Failed
- ⏭️ Skipped
- 👉 Current step

### Execution Flow

1. **Planning Phase**: Agent analyzes request and creates plan
2. **Execution Phase**: Steps executed sequentially
3. **Replanning Phase**: If step fails, plan is adjusted
4. **Completion**: All steps done or max iterations reached

## Example Tasks

### Task 1: File Creation

Request: "Create a Python file named test.py with a hello world function"

Expected plan:
1. Create file with function definition
2. Verify file was created

### Task 2: Code Execution

Request: "Write and run a Python script that calculates fibonacci(10)"

Expected plan:
1. Create Python file with fibonacci function
2. Execute the file
3. Display output

### Task 3: File Operations

Request: "Copy all .txt files from docs/ to backup/"

Expected plan:
1. List .txt files in docs/
2. Create backup/ directory
3. Copy each file

### Task 4: Complex Workflow

Request: "Create a project structure with main.py, utils.py, and README.md"

Expected plan:
1. Create main.py with basic structure
2. Create utils.py with helper functions
3. Create README.md with documentation
4. Verify all files exist

## Troubleshooting

### Issue: "Module not found"

Solution: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "API key error"

Solution: Check your API key in the config
```python
llm_config = LLMConfig(api_key="your-correct-key")
```

### Issue: "Timeout error"

Solution: Increase timeout in tool parameters
```python
state = AgentState(max_iterations=30)  # Increase from 20
```

### Issue: "Plan not executing"

Solution: Check the logs for errors. Enable debug logging:
```python
logger = setup_logger(level=logging.DEBUG)
```

## Advanced Usage

### Custom Tools

Add your own tool:

```python
# tools/my_tool.py
from .base import BaseTool, ToolResult

class MyTool(BaseTool):
    def __init__(self):
        self.name = "my_tool"
        self.description = "Does something useful"
        self.parameters = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            },
            "required": ["param1"]
        }

    async def execute(self, param1: str, **kwargs) -> ToolResult:
        # Your logic here
        return ToolResult(success=True, output="Done!")
```

Register in `agent/executor.py`:
```python
self.tools = {
    "my_tool": MyTool(),
    # ... other tools
}
```

### State Persistence

Save state to file:

```python
import json

# Save
with open("state.json", "w") as f:
    json.dump(final_state.to_dict(), f)

# Load
with open("state.json", "r") as f:
    state_dict = json.load(f)
    state = AgentState(**state_dict)
```

### Monitoring Progress

Add callbacks:

```python
def on_step_complete(step):
    print(f"Completed: {step.description}")

# In executor.py, after step completion:
on_step_complete(step)
```

## Best Practices

1. **Clear Requests**: Be specific about what you want
   - Good: "Create a Python file named calc.py with add and subtract functions"
   - Bad: "Make a calculator"

2. **Iterative Development**: Start simple, then add complexity
   - First: Get basic functionality working
   - Then: Add error handling, optimization, etc.

3. **Monitor Progress**: Watch the todo list to understand what's happening

4. **Handle Failures**: The agent will try to recover, but you can also adjust the request

5. **Use Appropriate Tools**:
   - File operations → file_editor
   - Code execution → python_executor
   - System commands → bash_executor

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [README.md](README.md) for detailed documentation
- Explore example.py for usage patterns
- Customize tools for your specific needs

## Support

For issues or questions:
1. Check the logs for error messages
2. Review the architecture documentation
3. Examine the example scripts
4. Debug with logging enabled
