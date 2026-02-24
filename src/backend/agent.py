"""OpenAI Agent configuration with MCP server integration.

Manages the singleton MCP server lifecycle and Agent instantiation.
The MCP server is started once at application startup and reused across requests.
Uses dynamic instructions via callable + context for per-request user_id injection.

Supports multiple LLM providers:
  - Groq (free tier): Set GROQ_API_KEY in .env
  - OpenAI (paid): Set OPENAI_API_KEY in .env
  - Auto-detects provider from available keys, or set LLM_PROVIDER explicitly.
"""

import os
import sys
import logging
from dataclasses import dataclass
from openai import AsyncOpenAI
from config import settings
from agents import Agent, Runner, RunContextWrapper, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

logger = logging.getLogger(__name__)

# Ensure OPENAI_API_KEY is in the OS environment for the openai-agents SDK (when using OpenAI)
if settings.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Singleton instances
_mcp_server: MCPServerStdio | None = None
_agent: Agent | None = None


@dataclass
class ChatContext:
    """Per-request context passed to the agent via Runner.run(context=...)."""
    user_id: str


def _resolve_provider() -> str:
    """Determine which LLM provider to use based on config and available keys."""
    if settings.llm_provider:
        return settings.llm_provider.lower()
    if settings.groq_api_key:
        return "groq"
    if settings.openai_api_key:
        return "openai"
    raise RuntimeError(
        "No LLM provider configured. Set GROQ_API_KEY (free) or OPENAI_API_KEY in .env"
    )


def _build_model():
    """Build the appropriate model instance for the resolved provider."""
    provider = _resolve_provider()

    if provider == "groq":
        logger.info(f"Using Groq provider with model: {settings.groq_model}")
        groq_client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
        )
        return OpenAIChatCompletionsModel(
            model=settings.groq_model,
            openai_client=groq_client,
        )
    elif provider == "openai":
        logger.info("Using OpenAI provider (default model)")
        # Return None — the Agent SDK uses its default OpenAI model
        return None
    else:
        raise RuntimeError(f"Unknown LLM provider: {provider}")


# System prompt template — user_id is injected per request via dynamic instructions
SYSTEM_PROMPT_TEMPLATE = """You are a helpful, friendly todo task manager assistant. You help users manage their tasks through natural language conversation.

The current user's ID is: {user_id}
You MUST pass this exact user_id as the first argument when calling ANY MCP tool.

## Tool Routing Rules

You have access to 5 tools for managing tasks. Route user intent as follows:

### add_task(user_id, title, description="")
Use when the user wants to ADD, CREATE, or REMEMBER something.
Examples:
- "Add a task to buy groceries" → add_task(user_id="{user_id}", title="Buy groceries")
- "I need to remember to pay bills" → add_task(user_id="{user_id}", title="Pay bills")
- "Remind me to call mom tonight" → add_task(user_id="{user_id}", title="Call mom tonight")

### list_tasks(user_id, status="all")
Use when the user wants to SEE, SHOW, or LIST tasks. Pass the appropriate status filter.
Examples:
- "Show me all my tasks" → list_tasks(user_id="{user_id}", status="all")
- "What's pending?" → list_tasks(user_id="{user_id}", status="pending")
- "What have I completed?" → list_tasks(user_id="{user_id}", status="completed")

### complete_task(user_id, task_id)
Use when the user says DONE, COMPLETE, FINISHED, or MARK as done.
Examples:
- "Mark task 3 as complete" → complete_task(user_id="{user_id}", task_id=3)
- "I finished task 1" → complete_task(user_id="{user_id}", task_id=1)

### delete_task(user_id, task_id)
Use when the user says DELETE, REMOVE, or CANCEL a task.
If the user refers to a task by name, call list_tasks first to find the task_id.
Examples:
- "Delete task 5" → delete_task(user_id="{user_id}", task_id=5)
- "Remove the meeting task" → first list_tasks to find it, then delete_task

### update_task(user_id, task_id, title=None, description=None)
Use when the user says CHANGE, UPDATE, RENAME, or EDIT a task.
Examples:
- "Change task 1 to 'Call mom tonight'" → update_task(user_id="{user_id}", task_id=1, title="Call mom tonight")
- "Update the description of task 2" → update_task with description

## Response Rules
- Always confirm actions with a friendly, conversational response
- Example: "Done! I've added 'Buy groceries' to your task list."
- Example: "I've marked 'Buy groceries' as complete."
- Format task lists as numbered lists showing task ID, title, and status
- Handle errors gracefully — if a tool returns an error, explain the issue in plain language
- Never expose raw JSON, tool output, or internal IDs unless displaying task lists
- Be concise, warm, and helpful
- If the user's intent is unclear, ask a brief clarifying question
"""


def dynamic_instructions(
    context: RunContextWrapper[ChatContext],
    agent: Agent[ChatContext],
) -> str:
    """Build per-request system prompt with user_id injected from context."""
    return SYSTEM_PROMPT_TEMPLATE.format(user_id=context.context.user_id)


async def startup_agent() -> None:
    """Initialize the MCP server and Agent at application startup."""
    global _mcp_server, _agent

    mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

    _mcp_server = MCPServerStdio(
        name="todo-task-server",
        params={
            "command": sys.executable,
            "args": [mcp_server_path],
        },
    )
    await _mcp_server.__aenter__()
    logger.info("MCP server started successfully")

    # Build the model (Groq or OpenAI)
    model = _build_model()

    agent_kwargs = dict(
        name="Todo Assistant",
        instructions=dynamic_instructions,
        mcp_servers=[_mcp_server],
    )
    if model is not None:
        agent_kwargs["model"] = model

    _agent = Agent(**agent_kwargs)
    logger.info(f"Agent initialized successfully (provider: {_resolve_provider()})")


async def shutdown_agent() -> None:
    """Clean up the MCP server at application shutdown."""
    global _mcp_server, _agent

    if _mcp_server is not None:
        await _mcp_server.__aexit__(None, None, None)
        logger.info("MCP server shut down")
    _mcp_server = None
    _agent = None


def get_agent() -> Agent:
    """Get the initialized Agent instance."""
    if _agent is None:
        raise RuntimeError("Agent not initialized. Call startup_agent() first.")
    return _agent
