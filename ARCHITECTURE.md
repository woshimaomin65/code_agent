# Code Agent Architecture

## Overview

This document describes the architecture of the Code Agent system, a LangGraph-based autonomous agent for code manipulation tasks.

## System Components

### 1. Configuration Layer (`config/`)

**LLMConfig** - Manages LLM connection settings
- API endpoint configuration
- Model selection
- Generation parameters (temperature, max_tokens)
- Supports any OpenAI-compatible API

### 2. Tools Layer (`tools/`)

**BaseTool** - Abstract base class for all tools
- Defines common interface
- Standardized result format (ToolResult)
- Schema generation for LLM

**FileEditorTool** - File system operations
- View files/directories
- Create/delete files
- Copy files/directories
- String replacement in files
- Line-based insertion

**PythonExecutorTool** - Python code execution
- Sandboxed execution environment
- Timeout control
- Output capture
- Error handling

**BashExecutorTool** - Shell command execution
- Async command execution
- Timeout control
- stdout/stderr capture

### 3. Agent Layer (`agent/`)

#### State Management (`state.py`)

**PlanStatus** - Enum for step states
- PENDING: Not started
- IN_PROGRESS: Currently executing
- COMPLETED: Successfully finished
- FAILED: Execution failed
- SKIPPED: Bypassed during replanning

**PlanStep** - Individual plan step
- Unique ID
- Description
- Tool and parameters
- Dependencies (other step IDs)
- Execution result/error
- Status tracking

**AgentState** - Complete agent state
- User request
- Plan (list of steps)
- Current step tracking
- Execution history
- Context and memory
- Control flags (needs_replan, is_complete)
- Iteration limits

Key methods:
- `get_current_step()`: Get currently executing step
- `get_next_pending_step()`: Find next executable step
- `get_todo_list()`: Format progress display
- `update_step_status()`: Update step state

#### Planning (`planner.py`)

**Planner** - Initial plan generation
- Analyzes user request
- Generates step-by-step plan
- Assigns tools to steps
- Defines dependencies
- Uses LLM for intelligent planning

Process:
1. Receive user request
2. Query LLM with available tools
3. Parse JSON plan response
4. Create PlanStep objects
5. Initialize AgentState

#### Execution (`executor.py`)

**Executor** - Step execution engine
- Manages tool registry
- Executes steps sequentially
- Respects dependencies
- Handles errors
- Updates state

Process:
1. Get next pending step (with satisfied dependencies)
2. Mark as IN_PROGRESS
3. Execute tool with parameters
4. Update status (COMPLETED/FAILED)
5. Trigger replanning if needed

#### Replanning (`replanner.py`)

**Replanner** - Dynamic plan adjustment
- Analyzes failures
- Generates recovery strategies
- Modifies/adds/skips steps

Strategies:
- **Modify**: Fix parameters of failed step
- **Add Steps**: Insert new steps
- **Skip**: Bypass non-critical failures
- **Alternative**: Replace with different approach

Process:
1. Identify failed steps
2. Query LLM with failure context
3. Parse replanning strategy
4. Apply changes to plan
5. Reset failed steps to PENDING

#### Workflow (`graph.py`)

**LangGraph Workflow** - State machine orchestration

Nodes:
- `plan`: Initial planning
- `execute`: Step execution
- `replan`: Plan adjustment

Edges:
- `plan → execute`: Start execution
- `execute → execute`: Continue (loop)
- `execute → replan`: Handle failures
- `execute → END`: Task complete
- `replan → execute`: Resume after replanning

Decision logic (`should_continue`):
- If `is_complete`: → END
- If `needs_replan`: → replan
- Otherwise: → execute

### 4. Utilities Layer (`utils/`)

**Logger** - Logging configuration
- Console output
- Optional file logging
- Configurable levels

## Data Flow

```
User Request
    ↓
[Planner] → Generate initial plan
    ↓
[Executor] → Execute step
    ↓
Success? → Continue to next step
    ↓
Failure? → [Replanner] → Adjust plan → Back to Executor
    ↓
All steps done? → END
```

## State Machine Diagram

```
┌─────────┐
│  START  │
└────┬────┘
     ↓
┌────────────┐
│   PLAN     │ (Generate initial plan)
└─────┬──────┘
      ↓
┌─────────────┐
│   EXECUTE   │◄──────┐
└──┬──┬───┬───┘       │
   │  │   │           │
   │  │   └─→[More]───┘
   │  │
   │  └─→[Failed]
   │         ↓
   │    ┌──────────┐
   │    │ REPLAN   │
   │    └────┬─────┘
   │         │
   │         └──────────┘
   │
   └─→[Complete]
         ↓
      ┌─────┐
      │ END │
      └─────┘
```

## Extension Points

### Adding New Tools

1. Inherit from `BaseTool`
2. Implement `execute()` method
3. Define `name`, `description`, `parameters`
4. Register in `Executor.tools`

### Customizing Planning

1. Modify `Planner.create_plan()`
2. Adjust system prompt
3. Change JSON schema
4. Add domain-specific logic

### Extending State

1. Add fields to `AgentState`
2. Update state methods
3. Modify serialization if needed

### Workflow Modifications

1. Add new nodes to graph
2. Define node functions
3. Add edges and conditions
4. Update decision logic

## Configuration

### LLM Settings

```python
LLMConfig(
    api_base="https://api.deepseek.com",
    api_key="your-key",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=4096
)
```

### Agent Settings

- `max_iterations`: Maximum execution loops
- `timeout`: Tool execution timeout
- Log level and output

## Error Handling

### Tool Errors
- Caught and stored in step.error
- Triggers replanning
- Can be skipped or retried

### LLM Errors
- JSON parsing fallbacks
- Default strategies
- Graceful degradation

### System Errors
- Logged with full traceback
- State preserved
- Can resume from checkpoint

## Performance Considerations

### Parallelization
- Currently sequential execution
- Can be extended for parallel steps
- Check dependencies before parallel execution

### Caching
- LLM responses can be cached
- Tool results can be memoized
- State snapshots for rollback

### Optimization
- Batch similar operations
- Minimize LLM calls
- Efficient state updates

## Security

### Sandboxing
- Python execution in separate process
- Timeout controls
- Limited builtins

### File Operations
- Path validation
- Permission checks
- Atomic operations where possible

### Command Execution
- Input sanitization
- Timeout enforcement
- Output size limits

## Future Enhancements

1. **Parallel Execution**: Execute independent steps concurrently
2. **Checkpointing**: Save/restore state for long-running tasks
3. **Human-in-the-Loop**: Request user input during execution
4. **Tool Learning**: Learn from execution patterns
5. **Multi-Agent**: Coordinate multiple specialized agents
6. **Streaming**: Real-time progress updates
7. **Visualization**: Web UI for plan visualization
8. **Metrics**: Track success rates, execution times
