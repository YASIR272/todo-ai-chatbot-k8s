from mcp.server.fastmcp import FastMCP
from sqlmodel import Session, select
from database import engine
from models import Task
import json


# Create the MCP server instance
mcp = FastMCP("todo-task-server")


@mcp.tool()
def add_task(user_id: str, title: str, description: str = "") -> str:
    """Create a new task for the user's todo list.

    Use this tool when the user wants to add, create, or remember something.
    Examples: "Add a task to buy groceries", "I need to remember to pay bills"

    Args:
        user_id: The authenticated user's unique identifier
        title: The task title (what needs to be done)
        description: Optional additional details about the task
    """
    if not title or not title.strip():
        return json.dumps({"error": "Title is required"})
    if len(title) > 255:
        return json.dumps({"error": "Title must be 255 characters or less"})

    with Session(engine) as session:
        task = Task(user_id=user_id, title=title.strip(), description=description if description else None)
        session.add(task)
        session.commit()
        session.refresh(task)
        return json.dumps({"task_id": task.id, "status": "created", "title": task.title})


@mcp.tool()
def list_tasks(user_id: str, status: str = "all") -> str:
    """Retrieve tasks from the user's todo list.

    Use this tool when the user asks to see, show, or list their tasks.
    Examples: "Show me all my tasks", "What's on my todo list?", "List completed tasks"

    Args:
        user_id: The authenticated user's unique identifier
        status: Filter tasks by status: 'all' (default), 'pending', or 'completed'
    """
    if status not in ("all", "pending", "completed"):
        return json.dumps({"error": "Invalid status filter. Must be 'all', 'pending', or 'completed'"})

    with Session(engine) as session:
        statement = select(Task).where(Task.user_id == user_id)
        if status == "pending":
            statement = statement.where(Task.completed == False)
        elif status == "completed":
            statement = statement.where(Task.completed == True)
        tasks = session.exec(statement).all()
        return json.dumps([{"id": t.id, "title": t.title, "completed": t.completed} for t in tasks])


def _parse_task_id(task_id) -> int:
    """Parse task_id from int or string (some LLMs pass string)."""
    return int(task_id)


@mcp.tool()
def complete_task(user_id: str, task_id: int) -> str:
    """Mark a task as complete.

    Use this tool when the user says they finished, completed, or are done with a task.
    Examples: "Mark task 3 as done", "I finished buying groceries", "Complete task 5"

    Args:
        user_id: The authenticated user's unique identifier
        task_id: The ID of the task to mark as complete
    """
    task_id = _parse_task_id(task_id)
    with Session(engine) as session:
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        task = session.exec(statement).first()
        if not task:
            return json.dumps({"error": "Task not found"})
        task.completed = True
        session.add(task)
        session.commit()
        return json.dumps({"task_id": task.id, "status": "completed", "title": task.title})


@mcp.tool()
def delete_task(user_id: str, task_id: int) -> str:
    """Remove a task from the user's todo list.

    Use this tool when the user wants to delete, remove, or cancel a task.
    Examples: "Delete task 2", "Remove the groceries task", "Cancel that task"

    Args:
        user_id: The authenticated user's unique identifier
        task_id: The ID of the task to delete
    """
    task_id = _parse_task_id(task_id)
    with Session(engine) as session:
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        task = session.exec(statement).first()
        if not task:
            return json.dumps({"error": "Task not found"})
        title = task.title
        session.delete(task)
        session.commit()
        return json.dumps({"task_id": task_id, "status": "deleted", "title": title})


@mcp.tool()
def update_task(user_id: str, task_id: int, title: str = "", description: str = "") -> str:
    """Modify a task's title or description.

    Use this tool when the user wants to change, update, rename, or edit a task.
    Examples: "Rename task 1 to Buy fruits", "Update the description of task 3"

    Args:
        user_id: The authenticated user's unique identifier
        task_id: The ID of the task to update
        title: New title for the task (optional if description is provided)
        description: New description for the task (optional if title is provided)
    """
    task_id = _parse_task_id(task_id)
    if not title and not description:
        return json.dumps({"error": "No fields to update"})
    if title and len(title) > 255:
        return json.dumps({"error": "Title must be 255 characters or less"})
    if title and not title.strip():
        return json.dumps({"error": "Title cannot be empty"})

    with Session(engine) as session:
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        task = session.exec(statement).first()
        if not task:
            return json.dumps({"error": "Task not found"})
        if title:
            task.title = title.strip()
        if description:
            task.description = description
        session.add(task)
        session.commit()
        session.refresh(task)
        return json.dumps({"task_id": task.id, "status": "updated", "title": task.title})


if __name__ == "__main__":
    mcp.run(transport="stdio")
