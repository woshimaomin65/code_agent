"""Main entry point for the code agent."""
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from config import LLMConfig
from agent import AgentState, create_agent_graph
from utils import setup_logger


async def main():
    """Main function."""
    # Setup logger
    logger = setup_logger()

    # Load LLM config
    llm_config = LLMConfig(
        api_base="https://api.deepseek.com",
        api_key="sk-13b88e3a2e2d44398eb928e84dfef13a",
        model="deepseek-chat",
        response_format="text",
        temperature=0.7,
        streaming=True,
        max_tokens=30000
    )
    #llm_config = LLMConfig(
    #    api_base="http://192.168.18.201:30847/v1",
    #    api_key="anything",
    #    model="/data/meiyeai/model-server-qwen3/models/qwen3_32b_awq",
    #    response_format="text",
    #    temperature=0.7,
    #    max_tokens=30000,
    #    streaming=True,
    #    extra_body={
    #    "chat_template_kwargs": {"enable_thinking": False},
    #    "separate_reasoning": True
    #})

    logger.info("🚀 Starting Code Agent")
    logger.info(f"Using model: {llm_config.model}")

    # Create agent graph
    agent = create_agent_graph(llm_config)

    # Custom style for prompt
    style = Style.from_dict({
        'prompt': '#00aa00 bold',
    })

    # Get user request with better input handling (async version)
    session = PromptSession(style=style)
    user_request = await session.prompt_async("📝 Enter your request: ")

    # Initialize state
    initial_state = AgentState(
        user_request=user_request,
        max_iterations=20
    )

    logger.info(f"\n📋 User Request: {user_request}\n")

    # Run agent
    try:
        final_state_dict = await agent.ainvoke(initial_state)

        # Convert dictionary back to AgentState object
        final_state = AgentState(**final_state_dict)

        # Print final results
        print("\n" + "="*60)
        print("📊 Final Results")
        print("="*60)
        print(final_state.get_todo_list())
        print("\n✅ Task completed!" if final_state.is_complete else "\n⚠️ Task incomplete")

        # Print completed steps results
        print("\n📝 Execution Summary:")
        for step in final_state.plan:
            if step.result:
                print(f"\nStep {step.id}: {step.description}")
                print(f"Result: {step.result[:200]}...")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
