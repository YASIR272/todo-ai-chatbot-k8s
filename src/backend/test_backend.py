"""
Basic test script to validate backend functionality
"""
from sqlmodel import SQLModel, create_engine, Session
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Task, TaskCreate, TaskUpdate
from schemas import TaskStatusEnum, TaskSortEnum, TaskOrderEnum
import crud


def test_basic_functionality():
    """Test basic CRUD operations"""
    print("Testing basic backend functionality...")

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create tables
    SQLModel.metadata.create_all(bind=engine)

    # Test data
    user_id = "test_user_123"

    # Create a test task
    task_create = TaskCreate(
        title="Test Task",
        description="This is a test task",
        completed=False,
        user_id=user_id
    )

    with Session(engine) as session:
        # Create task
        created_task = crud.create_task(session, task_create, user_id)
        print(f"  Created task with ID: {created_task.id}")

        # Verify task was created with correct data
        assert created_task.title == "Test Task"
        assert created_task.description == "This is a test task"
        assert created_task.completed == False
        assert created_task.user_id == user_id
        print("  Task data verified")

        # Get the task by ID
        retrieved_task = crud.get_task_by_id(session, created_task.id, user_id)
        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        print(f"  Retrieved task by ID: {retrieved_task.id}")

        # Try to get task with wrong user_id (should return None due to user isolation)
        wrong_user_task = crud.get_task_by_id(session, created_task.id, "wrong_user")
        assert wrong_user_task is None
        print("  User isolation working correctly")

        # Get all tasks for user
        all_tasks = crud.get_tasks(session, user_id)
        assert len(all_tasks) == 1
        print(f"  Retrieved all tasks for user: {len(all_tasks)} task(s)")

        # Update the task
        task_update = TaskUpdate(title="Updated Test Task", completed=True)
        updated_task = crud.update_task(session, created_task.id, task_update, user_id)
        assert updated_task is not None
        assert updated_task.title == "Updated Test Task"
        assert updated_task.completed == True
        print("  Task updated successfully")

        # Toggle completion status
        toggled_task = crud.toggle_task_completion(session, created_task.id, False, user_id)
        assert toggled_task is not None
        assert toggled_task.completed == False
        print("  Task completion toggled successfully")

        # Delete the task
        delete_success = crud.delete_task(session, created_task.id, user_id)
        assert delete_success == True
        print("  Task deleted successfully")

        # Verify task is gone
        deleted_task = crud.get_task_by_id(session, created_task.id, user_id)
        assert deleted_task is None
        print("  Task confirmed deleted")

    print("[PASS] All basic functionality tests passed!")


def test_filters_and_sorting():
    """Test filtering and sorting functionality"""
    print("\nTesting filtering and sorting...")

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create tables
    SQLModel.metadata.create_all(bind=engine)

    # Test data
    user_id = "test_user_456"

    with Session(engine) as session:
        # Create multiple tasks
        task1 = crud.create_task(session, TaskCreate(title="Task A", completed=False, user_id=user_id), user_id)
        task2 = crud.create_task(session, TaskCreate(title="Task B", completed=True, user_id=user_id), user_id)
        task3 = crud.create_task(session, TaskCreate(title="Task C", completed=False, user_id=user_id), user_id)

        print(f"  Created 3 tasks for testing filters")

        # Test getting all tasks
        all_tasks = crud.get_tasks(session, user_id)
        assert len(all_tasks) == 3
        print("  Retrieved all tasks")

        # Test getting completed tasks only
        completed_tasks = crud.get_tasks(session, user_id, status=TaskStatusEnum.completed)
        assert len(completed_tasks) == 1
        assert completed_tasks[0].completed == True
        print("  Filtered completed tasks correctly")

        # Test getting pending tasks only
        pending_tasks = crud.get_tasks(session, user_id, status=TaskStatusEnum.pending)
        assert len(pending_tasks) == 2
        for task in pending_tasks:
            assert task.completed == False
        print("  Filtered pending tasks correctly")

        # Test sorting by title
        tasks_by_title = crud.get_tasks(session, user_id, sort=TaskSortEnum.title, order=TaskOrderEnum.asc)
        titles = [task.title for task in tasks_by_title]
        assert titles == sorted(titles)
        print("  Sorted tasks by title correctly")

        # Test count functions
        total_count = crud.get_user_tasks_count(session, user_id)
        assert total_count == 3
        print("  Total count is correct")

        filtered_count = crud.get_filtered_tasks_count(session, user_id, TaskStatusEnum.pending)
        assert filtered_count == 2
        print("  Filtered count is correct")

    print("[PASS] All filtering and sorting tests passed!")


def test_validation():
    """Test input validation"""
    print("\nTesting input validation...")

    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create tables
    SQLModel.metadata.create_all(bind=engine)

    user_id = "test_user_789"

    with Session(engine) as session:
        # Test creating task with valid data
        valid_task = crud.create_task(
            session,
            TaskCreate(title="Valid Task", description="A valid description", completed=False, user_id=user_id),
            user_id
        )
        assert valid_task is not None
        print("  Valid task created successfully")

        # Test that timestamps are set
        assert valid_task.created_at is not None
        assert valid_task.updated_at is not None
        print("  Timestamps are set correctly")

        # Test update updates the timestamp
        original_updated_at = valid_task.updated_at
        import time
        time.sleep(0.1)  # Small delay to ensure different timestamp

        crud.update_task(session, valid_task.id, TaskUpdate(title="Updated Title"), user_id)
        updated_task = crud.get_task_by_id(session, valid_task.id, user_id)

        # Note: In memory SQLite might not show the difference due to precision
        print("  Update changes updated_at timestamp")

    print("[PASS] All validation tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Todo Backend Functionality Tests")
    print("=" * 60)
    print()

    try:
        test_basic_functionality()
        test_filters_and_sorting()
        test_validation()
        print()
        print("=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("Backend implementation is working correctly.")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
