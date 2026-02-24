"""Chat endpoint router for AI agent interactions.

Provides POST /api/{user_id}/chat for processing natural language messages
through the OpenAI agent with MCP tool access, with conversation persistence.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from agents import Runner
from agent import get_agent, ChatContext
from auth import get_current_user_id
from database import get_session
from models import Conversation, Message
from schemas import ChatRequest, ChatResponse, ToolCallInfo

logger = logging.getLogger(__name__)

router = APIRouter()

AGENT_TIMEOUT_SECONDS = 30
MAX_HISTORY_MESSAGES = 50


def get_effective_user_id(user_id: str, current_user_id: str) -> str:
    """Validate path user_id matches authenticated user. Demo mode uses path user_id."""
    if current_user_id == "demo-user":
        return user_id
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access another user's data",
        )
    return current_user_id


@router.post("/api/{user_id}/chat", response_model=ChatResponse)
async def chat(
    user_id: str,
    request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    """Process a chat message through the AI agent.

    Accepts a natural language message, runs it through the OpenAI agent
    with MCP tool access, persists all messages, and returns the response.
    """
    # Validate user identity
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # T010: Validate message is not empty
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    # T012/T015: Get or create conversation
    if request.conversation_id is not None:
        # Load existing conversation with ownership validation (T020/US6)
        conversation = session.get(Conversation, request.conversation_id)
        if conversation is None or conversation.user_id != effective_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=effective_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    # T013: Load conversation history (last N messages)
    history_query = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    history_messages = session.exec(history_query).all()

    # Truncate to last MAX_HISTORY_MESSAGES
    if len(history_messages) > MAX_HISTORY_MESSAGES:
        history_messages = history_messages[-MAX_HISTORY_MESSAGES:]

    # T014: Store user message before agent run
    user_message = Message(
        user_id=effective_user_id,
        conversation_id=conversation.id,
        role="user",
        content=request.message.strip(),
        created_at=datetime.now(timezone.utc),
    )
    session.add(user_message)
    session.commit()

    # Build input messages from history + new message
    input_messages = []
    for msg in history_messages:
        input_messages.append({"role": msg.role, "content": msg.content})
    input_messages.append({"role": "user", "content": request.message.strip()})

    # Get the agent
    try:
        agent = get_agent()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task service temporarily unavailable",
        )

    # Run the agent with timeout — context provides per-request user_id
    try:
        result = await asyncio.wait_for(
            Runner.run(
                agent,
                input_messages,
                context=ChatContext(user_id=effective_user_id),
            ),
            timeout=AGENT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out",
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "mcp" in error_msg or "connection" in error_msg or "subprocess" in error_msg:
            logger.error(f"MCP server error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task service temporarily unavailable",
            )
        logger.error(f"Agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service temporarily unavailable",
        )

    # Extract response text
    response_text = result.final_output or "I'm sorry, I couldn't process that request."

    # T014: Store assistant response after agent run
    assistant_message = Message(
        user_id=effective_user_id,
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        created_at=datetime.now(timezone.utc),
    )
    session.add(assistant_message)
    session.commit()

    # Extract tool calls from result
    tool_calls = _extract_tool_calls(result)

    return ChatResponse(
        conversation_id=conversation.id,
        response=response_text,
        tool_calls=tool_calls,
    )


def _extract_tool_calls(result) -> list[ToolCallInfo]:
    """Extract tool call information from the agent's RunResult."""
    tool_calls = []
    for item in result.new_items:
        if hasattr(item, "raw_item") and hasattr(item.raw_item, "type"):
            if item.raw_item.type == "function_call":
                tool_call_info = ToolCallInfo(
                    tool_name=getattr(item.raw_item, "name", "unknown"),
                    arguments=_parse_arguments(getattr(item.raw_item, "arguments", "{}")),
                    result="",
                )
                tool_calls.append(tool_call_info)
            elif item.raw_item.type == "function_call_output":
                output_text = getattr(item.raw_item, "output", "")
                for tc in reversed(tool_calls):
                    if tc.result == "":
                        tc.result = output_text
                        break
    return tool_calls


def _parse_arguments(args_str: str) -> dict:
    """Parse arguments string to dict, handling JSON or raw strings."""
    try:
        return json.loads(args_str)
    except (json.JSONDecodeError, TypeError):
        return {"raw": str(args_str)}
