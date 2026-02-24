from sqlmodel import Session, select, func
from typing import List, Optional
from models import Task, TaskCreate, TaskUpdate
from schemas import TaskStatusEnum, TaskSortEnum, TaskOrderEnum
from datetime import datetime


def create_task(db_session: Session, task: TaskCreate, user_id: str) -> Task:
    """Create a new task for a user"""
    db_task = Task(**task.model_dump())
    db_task.user_id = user_id
    db_task.created_at = datetime.utcnow()
    db_task.updated_at = datetime.utcnow()

    db_session.add(db_task)
    db_session.commit()
    db_session.refresh(db_task)
    return db_task


def get_task_by_id(db_session: Session, task_id: int, user_id: str) -> Optional[Task]:
    """Get a specific task by ID for a user"""
    statement = select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
    return db_session.exec(statement).first()


def get_tasks(
    db_session: Session,
    user_id: str,
    status: TaskStatusEnum = TaskStatusEnum.all,
    sort: TaskSortEnum = TaskSortEnum.created,
    order: TaskOrderEnum = TaskOrderEnum.desc,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Task]:
    """Get tasks for a user with filtering and sorting"""
    statement = select(Task).where(Task.user_id == user_id)

    # Apply status filter
    if status != TaskStatusEnum.all:
        if status == TaskStatusEnum.completed:
            statement = statement.where(Task.completed == True)
        elif status == TaskStatusEnum.pending:
            statement = statement.where(Task.completed == False)

    # Apply sorting
    if sort == TaskSortEnum.created:
        if order == TaskOrderEnum.asc:
            statement = statement.order_by(Task.created_at.asc())
        else:
            statement = statement.order_by(Task.created_at.desc())
    elif sort == TaskSortEnum.updated:
        if order == TaskOrderEnum.asc:
            statement = statement.order_by(Task.updated_at.asc())
        else:
            statement = statement.order_by(Task.updated_at.desc())
    elif sort == TaskSortEnum.title:
        if order == TaskOrderEnum.asc:
            statement = statement.order_by(Task.title.asc())
        else:
            statement = statement.order_by(Task.title.desc())
    elif sort == TaskSortEnum.priority:
        # Priority order: high > normal > low (desc) or low > normal > high (asc)
        if order == TaskOrderEnum.asc:
            statement = statement.order_by(Task.priority.asc())
        else:
            statement = statement.order_by(Task.priority.desc())
    elif sort == TaskSortEnum.due_date:
        # Tasks with no due date come last
        if order == TaskOrderEnum.asc:
            statement = statement.order_by(Task.due_date.asc().nullslast())
        else:
            statement = statement.order_by(Task.due_date.desc().nullslast())

    # Apply limit and offset
    if limit is not None:
        statement = statement.limit(limit)
    if offset is not None:
        statement = statement.offset(offset)

    return db_session.exec(statement).all()


def update_task(db_session: Session, task_id: int, task_update: TaskUpdate, user_id: str) -> Optional[Task]:
    """Update a task for a user"""
    db_task = get_task_by_id(db_session, task_id, user_id)
    if not db_task:
        return None

    # Update fields that are provided
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    # Update the updated_at timestamp
    db_task.updated_at = datetime.utcnow()

    db_session.add(db_task)
    db_session.commit()
    db_session.refresh(db_task)
    return db_task


def delete_task(db_session: Session, task_id: int, user_id: str) -> bool:
    """Delete a task for a user"""
    db_task = get_task_by_id(db_session, task_id, user_id)
    if not db_task:
        return False

    db_session.delete(db_task)
    db_session.commit()
    return True


def toggle_task_completion(db_session: Session, task_id: int, completed: bool, user_id: str) -> Optional[Task]:
    """Toggle completion status of a task for a user"""
    db_task = get_task_by_id(db_session, task_id, user_id)
    if not db_task:
        return None

    db_task.completed = completed
    db_task.updated_at = datetime.utcnow()

    db_session.add(db_task)
    db_session.commit()
    db_session.refresh(db_task)
    return db_task


def get_user_tasks_count(db_session: Session, user_id: str) -> int:
    """Get total count of tasks for a user"""
    statement = select(func.count(Task.id)).where(Task.user_id == user_id)
    return db_session.exec(statement).one()


def get_filtered_tasks_count(
    db_session: Session,
    user_id: str,
    status: TaskStatusEnum = TaskStatusEnum.all
) -> int:
    """Get count of filtered tasks for a user"""
    statement = select(func.count(Task.id)).where(Task.user_id == user_id)

    if status != TaskStatusEnum.all:
        if status == TaskStatusEnum.completed:
            statement = statement.where(Task.completed == True)
        elif status == TaskStatusEnum.pending:
            statement = statement.where(Task.completed == False)

    return db_session.exec(statement).one()