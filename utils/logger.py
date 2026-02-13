"""Logging utilities."""
import logging
import sys
from typing import Optional, List, Any, Tuple
from langchain_openai import ChatOpenAI


def setup_logger(
    name: str = "code_agent",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Setup logger with console and optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def log_llm_interaction(
    logger: logging.Logger,
    module: str,
    messages: List[Any],
    response: str,
    truncate: int = 500
) -> None:
    """Log LLM input and output for debugging.

    Args:
        logger: Logger instance
        module: Name of the module (e.g., 'planner', 'executor', 'replanner')
        messages: List of messages sent to LLM
        response: Response from LLM
        truncate: Maximum length for truncating long messages (0 = no truncation)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🤖 LLM Interaction - {module.upper()}")
    logger.info(f"{'='*60}")

    # Log input messages
    logger.info("📤 INPUT:")
    for i, msg in enumerate(messages):
        role = getattr(msg, 'type', 'unknown')
        content = getattr(msg, 'content', str(msg))

        if truncate > 0 and len(content) > truncate:
            content = content[:truncate] + f"... (truncated, total: {len(content)} chars)"

        logger.info(f"  Message {i+1} [{role}]:")
        logger.info(f"  {content}\n")

    # Log output response
    logger.info("📥 OUTPUT:")
    if truncate > 0 and len(response) > truncate:
        logger.info(f"  {response[:truncate]}... (truncated, total: {len(response)} chars)")
    else:
        logger.info(f"  {response}")

    logger.info(f"{'='*60}\n")


def strip_think_tags(content: str) -> str:
    """Remove <think>...</think> tags from content.

    Args:
        content: Text that may contain think tags

    Returns:
        Content with think tags removed
    """
    if '<think>' in content and '</think>' in content:
        # Remove everything from <think> to </think>
        content = content.rsplit('</think>', 1)[1].strip()
    return content


async def invoke_llm_with_streaming(
    llm: ChatOpenAI,
    messages: List[Any],
    streaming: bool = False,
    module: str = "llm",
    logger: Optional[logging.Logger] = None
) -> Tuple[str, str]:
    """Invoke LLM with optional streaming and think tag handling.

    Args:
        llm: ChatOpenAI instance
        messages: List of messages to send
        streaming: Whether to use streaming mode
        module: Module name for logging
        logger: Logger instance for logging interactions

    Returns:
        Tuple of (raw_content, cleaned_content) where cleaned_content has think tags removed
    """
    if streaming:
        # Streaming mode
        print(f"\n{'='*60}")
        print(f"🤖 {module.upper()} - Streaming Response")
        print(f"{'='*60}")

        full_content = ""
        async for chunk in llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end='', flush=True)
                full_content += chunk.content

        print(f"\n{'='*60}\n")

        # Strip think tags from final content
        cleaned_content = strip_think_tags(full_content)

        # Log the interaction
        if logger:
            log_llm_interaction(
                logger,
                module,
                messages,
                cleaned_content,
                truncate=500
            )

        return full_content, cleaned_content
    else:
        # Non-streaming mode
        response = await llm.ainvoke(messages)
        raw_content = response.content
        cleaned_content = strip_think_tags(raw_content)

        # Log the interaction
        if logger:
            log_llm_interaction(
                logger,
                module,
                messages,
                cleaned_content,
                truncate=500
            )

        return raw_content, cleaned_content
