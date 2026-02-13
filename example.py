"""Example usage of the code agent."""
import asyncio
from config import LLMConfig
from agent import AgentState, create_agent_graph
from utils import setup_logger


async def run_example(user_request: str, llm_config: LLMConfig):
    """Run an example request."""
    logger = setup_logger()

    logger.info(f"\n{'='*60}")
    logger.info(f"Running Example: {user_request}")
    logger.info(f"{'='*60}\n")

    # Create agent
    agent = create_agent_graph(llm_config)

    # Initialize state
    initial_state = AgentState(
        user_request=user_request,
        max_iterations=15
    )

    # Run agent
    try:
        final_state = await agent.ainvoke(initial_state)

        # Print results
        print("\n" + "="*60)
        print("📊 Results")
        print("="*60)
        print(final_state.get_todo_list())

        return final_state

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return None


async def main():
    """Run multiple examples."""
    # Configure LLM
    llm_config = LLMConfig(
        api_base="https://api.deepseek.com",
        api_key="sk-13b88e3a2e2d44398eb928e84dfef13a",
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096
    )

    # Example 1: Simple file creation
    await run_example(
        "Create a Python file named hello.py that prints 'Hello, World!'",
        llm_config
    )

    # Example 2: Multiple operations
    # await run_example(
    #     "Create a directory named 'test_project', then create a Python file inside it with a fibonacci function",
    #     llm_config
    # )

    # Example 3: Code execution
    # await run_example(
    #     "Write and execute a Python script that calculates the sum of numbers from 1 to 100",
    #     llm_config
    # )


if __name__ == "__main__":
    asyncio.run(main())
