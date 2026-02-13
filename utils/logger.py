"""Logging utilities."""
import logging
import sys
from typing import Optional, List, Any


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
