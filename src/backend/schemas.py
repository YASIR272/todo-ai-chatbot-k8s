from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PriorityEnum(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TaskStatusEnum(str, Enum):
    all = "all"
    pending = "pending"
    completed = "completed"


class TaskSortEnum(str, Enum):
    created = "created"
    updated = "updated"
    title = "title"
    priority = "priority"
    due_date = "due_date"


class TaskOrderEnum(str, Enum):
    asc = "asc"
    desc = "desc"


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: str
    priority: str = "normal"
    due_date: Optional[datetime] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: Optional[bool] = False
    priority: Optional[str] = "normal"
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskToggleComplete(BaseModel):
    completed: bool


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    priority: str = "normal"
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total_count: int
    filtered_count: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[dict] = None


class TaskFilterParams(BaseModel):
    status: TaskStatusEnum = TaskStatusEnum.all
    sort: TaskSortEnum = TaskSortEnum.created
    order: TaskOrderEnum = TaskOrderEnum.desc
    limit: Optional[int] = None
    offset: Optional[int] = None


class ToggleCompleteResponse(BaseModel):
    id: int
    completed: bool
    updated_at: datetime


# --- Chat Schemas (Feature 005) ---

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ToolCallInfo(BaseModel):
    tool_name: str
    arguments: dict
    result: str


class ChatResponse(BaseModel):
    conversation_id: int
    response: str
    tool_calls: List[ToolCallInfo] = []