from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Optional
from database import get_session
from auth import get_current_user_id
from models import Task, TaskCreate, TaskUpdate, TaskToggleComplete
import crud
from schemas import (
    TaskResponse, TaskListResponse, TaskCreate as SchemaTaskCreate,
    TaskUpdate as SchemaTaskUpdate, TaskToggleComplete as SchemaTaskToggleComplete,
    TaskFilterParams, ErrorResponse, ToggleCompleteResponse, TaskStatusEnum,
    TaskSortEnum, TaskOrderEnum
)

router = APIRouter(prefix="/api/{user_id}", tags=["tasks"])


def get_effective_user_id(user_id: str, current_user_id: str) -> str:
    """
    Get the effective user ID for operations.
    In demo mode (demo-user), use the path user_id.
    Otherwise, verify the authenticated user matches the path.
    """
    # Demo mode: allow access with path user_id
    if current_user_id == "demo-user":
        return user_id

    # Authenticated mode: verify user matches
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access another user's tasks"
        )
    return current_user_id


@router.get("/tasks", response_model=TaskListResponse)
def get_tasks(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session),
    status_param: TaskStatusEnum = Query(TaskStatusEnum.all, alias="status"),
    sort: TaskSortEnum = Query(TaskSortEnum.created),
    order: TaskOrderEnum = Query(TaskOrderEnum.desc),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0)
):
    """
    Get all tasks for a user with optional filtering and sorting
    """
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # Get tasks with filters
    tasks = crud.get_tasks(
        db_session=db,
        user_id=effective_user_id,
        status=status_param,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset
    )

    # Get counts
    total_count = crud.get_user_tasks_count(db, effective_user_id)
    filtered_count = crud.get_filtered_tasks_count(db, effective_user_id, status_param)

    # Convert to response format
    task_responses = [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            completed=task.completed,
            user_id=task.user_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            priority=task.priority,
            due_date=task.due_date
        )
        for task in tasks
    ]

    return TaskListResponse(
        tasks=task_responses,
        total_count=total_count,
        filtered_count=len(task_responses)
    )


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    user_id: str,
    task_create: SchemaTaskCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """
    Create a new task for a user
    """
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # Create the task - convert schema to model with user_id
    task_data = task_create.model_dump()
    task_data['user_id'] = effective_user_id
    db_task = crud.create_task(
        db_session=db,
        task=TaskCreate(**task_data),
        user_id=effective_user_id
    )

    return TaskResponse(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        completed=db_task.completed,
        user_id=db_task.user_id,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        priority=db_task.priority,
        due_date=db_task.due_date
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """
    Get a specific task by ID for a user
    """
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # Get the task
    db_task = crud.get_task_by_id(db_session=db, task_id=task_id, user_id=effective_user_id)

    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return TaskResponse(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        completed=db_task.completed,
        user_id=db_task.user_id,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        priority=db_task.priority,
        due_date=db_task.due_date
    )


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    user_id: str,
    task_id: int,
    task_update: SchemaTaskUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """
    Update a specific task for a user
    """
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # Update the task
    updated_task = crud.update_task(
        db_session=db,
        task_id=task_id,
        task_update=TaskUpdate(**task_update.model_dump(exclude_unset=True)),
        user_id=effective_user_id
    )

    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return TaskResponse(
        id=updated_task.id,
        title=updated_task.title,
        description=updated_task.description,
        completed=updated_task.completed,
        user_id=updated_task.user_id,
        created_at=updated_task.created_at,
        updated_at=updated_task.updated_at,
        priority=updated_task.priority,
        due_date=updated_task.due_date
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """
    Delete a specific task for a user
    """
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # Delete the task
    success = crud.delete_task(db_session=db, task_id=task_id, user_id=effective_user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Return 204 No Content
    return


@router.patch("/tasks/{task_id}/complete", response_model=ToggleCompleteResponse)
def toggle_task_complete(
    user_id: str,
    task_id: int,
    task_toggle: SchemaTaskToggleComplete,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """
    Toggle completion status of a specific task for a user
    """
    effective_user_id = get_effective_user_id(user_id, current_user_id)

    # Toggle the task completion
    updated_task = crud.toggle_task_completion(
        db_session=db,
        task_id=task_id,
        completed=task_toggle.completed,
        user_id=effective_user_id
    )

    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return ToggleCompleteResponse(
        id=updated_task.id,
        completed=updated_task.completed,
        updated_at=updated_task.updated_at
    )
