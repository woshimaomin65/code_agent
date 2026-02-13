"""LangGraph workflow definition."""
from typing import Literal
from langgraph.graph import StateGraph, END
from .state import AgentState
from .planner import Planner
from .executor import Executor
from .replanner import Replanner
from config.llm_config import LLMConfig


def should_continue(state: AgentState) -> Literal["replan", "execute", "end"]:
    """Determine next node based on state."""
    if state.is_complete:
        return "end"
    elif state.needs_replan:
        return "replan"
    else:
        return "execute"


def create_agent_graph(llm_config: LLMConfig) -> StateGraph:
    """Create the agent workflow graph."""
    # Initialize components
    planner = Planner(llm_config)
    executor = Executor(llm_config)  # Pass llm_config for goal verification
    replanner = Replanner(llm_config)

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("plan", planner.create_plan)
    workflow.add_node("execute", executor.execute_step)
    workflow.add_node("replan", replanner.replan)

    # Add edges
    workflow.set_entry_point("plan")

    # From plan, go to execute
    workflow.add_edge("plan", "execute")

    # From execute, decide next action
    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "execute": "execute",  # Continue executing
            "replan": "replan",    # Need to replan
            "end": END             # Task complete
        }
    )

    # From replan, go back to execute
    workflow.add_edge("replan", "execute")

    return workflow.compile()
