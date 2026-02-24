from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Index, text, String, Text
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class PriorityEnum(str, Enum):
    """Priority levels for tasks"""
    low = "low"
    normal = "normal"
    high = "high"


class TaskBase(SQLModel):
    """Base model for Task with common fields"""
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False, sa_column_kwargs={"index": True})  # Index for efficient status filtering
    user_id: str = Field(sa_column_kwargs={"index": True})  # Index for efficient user-based queries
    priority: str = Field(default="normal")  # low, normal, high
    due_date: Optional[datetime] = Field(default=None)  # Optional due date


class Task(TaskBase, table=True):
    """Task model for database table"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, 
                         server_default=text("CURRENT_TIMESTAMP"), 
                         onupdate=datetime.utcnow)
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_user_completed', 'user_id', 'completed'),  # Composite index for user and status queries
    )


class TaskRead(TaskBase):
    """Schema for reading task data (includes ID and timestamps)"""
    id: int
    created_at: datetime
    updated_at: datetime
    priority: str
    due_date: Optional[datetime]


class TaskCreate(SQLModel):
    """Schema for creating a new task (user_id provided separately)"""
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    user_id: Optional[str] = None  # Optional here, set by the route
    priority: str = Field(default="normal")  # low, normal, high
    due_date: Optional[datetime] = None  # Optional due date


class TaskUpdate(SQLModel):
    """Schema for updating an existing task"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: Optional[bool] = None
    priority: Optional[str] = None  # low, normal, high
    due_date: Optional[datetime] = None  # Optional due date


class TaskToggleComplete(SQLModel):
    """Schema for toggling task completion status"""
    completed: bool


class Conversation(SQLModel, table=True):
    """Conversation model for database table"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(sa_column_kwargs={"index": True})  # Index for efficient user-based queries
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False,
                         server_default=text("CURRENT_TIMESTAMP"),
                         onupdate=datetime.utcnow)
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_conversation_user_id', 'user_id'),  # Index on user_id for efficient user queries
    )


class Message(SQLModel, table=True):
    """Message model for database table"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(sa_column_kwargs={"index": True})  # Index for efficient user-based queries
    conversation_id: int = Field(foreign_key="conversation.id")  # Foreign Key to Conversation.id
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str = Field(sa_column=Column(Text, nullable=False))  # Text column for message content
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_message_user_id', 'user_id'),  # Index on user_id for efficient user queries
    )