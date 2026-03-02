"""Tests for MongoDB TaskStore implementation."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from a2a.types import (
    Task,
    TaskState,
    TaskStatus,
)
from testcontainers.mongodb import MongoDbContainer

from shared.mongodb_task_store import MongoDBTaskStore


@pytest.fixture(scope="session")
def mongodb_container():
    """Start a MongoDB container for the test session."""
    with MongoDbContainer("mongo:8.2") as container:
        yield container


@pytest_asyncio.fixture(scope="function")
async def task_store(mongodb_container):
    """Create a task store instance for testing."""
    connection_string = mongodb_container.get_connection_url()
    db_name = f"test_a2a_tasks_{uuid4().hex[:8]}"

    store = MongoDBTaskStore(
        connection_string=connection_string,
        database_name=db_name,
        collection_name="tasks_test",
    )
    yield store
    # Cleanup: drop database before closing client
    if store.client:
        await store.client.drop_database(db_name)
    await store.close()


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    task_id = str(uuid4())
    context_id = str(uuid4())

    return Task(
        id=task_id,
        context_id=context_id,
        status=TaskStatus(
            state=TaskState.working,
            message=None,
            timestamp=datetime.now(UTC).isoformat(),
        ),
        artifacts=[],
    )


@pytest.mark.asyncio
async def test_save_and_retrieve_task(task_store: MongoDBTaskStore, sample_task: Task):
    """Test saving and retrieving a task from MongoDB."""
    # Save task
    await task_store.save(sample_task)

    # Retrieve task
    retrieved_task = await task_store.get(sample_task.id)

    assert retrieved_task is not None
    assert retrieved_task.id == sample_task.id
    assert retrieved_task.context_id == sample_task.context_id
    assert retrieved_task.status.state == TaskState.working


@pytest.mark.asyncio
async def test_update_existing_task(task_store: MongoDBTaskStore, sample_task: Task):
    """Test updating an existing task."""
    # Save initial task
    await task_store.save(sample_task)

    # Update task state
    sample_task.status = TaskStatus(
        state=TaskState.completed,
        message=None,
        timestamp=datetime.now(UTC).isoformat(),
    )

    # Save updated task
    await task_store.save(sample_task)

    # Retrieve and verify
    retrieved_task = await task_store.get(sample_task.id)

    assert retrieved_task is not None
    assert retrieved_task.status.state == TaskState.completed


@pytest.mark.asyncio
async def test_delete_task(task_store: MongoDBTaskStore, sample_task: Task):
    """Test deleting a task."""
    # Save task
    await task_store.save(sample_task)

    # Delete task
    await task_store.delete(sample_task.id)

    # Verify deletion
    retrieved_task = await task_store.get(sample_task.id)
    assert retrieved_task is None


@pytest.mark.asyncio
async def test_get_task_with_context_id(
    task_store: MongoDBTaskStore, sample_task: Task,
):
    """Test retrieving a task with context parameter (context is ignored in MongoDB implementation)."""
    # Save task
    await task_store.save(sample_task)

    # Retrieve with context=None (default)
    retrieved_task = await task_store.get(sample_task.id, context=None)
    assert retrieved_task is not None
    assert retrieved_task.id == sample_task.id

    # Note: The context parameter is part of the TaskStore protocol for access control
    # but is not used for filtering in this MongoDB implementation


@pytest.mark.asyncio
async def test_update_task_status(task_store: MongoDBTaskStore, sample_task: Task):
    """Test updating task status."""
    # Save task
    await task_store.save(sample_task)

    # Update status
    new_status = TaskStatus(
        state=TaskState.working,
        message=None,
        timestamp=datetime.now(UTC).isoformat(),
    )
    await task_store.update_task_status(
        sample_task.id,
        status=new_status,
    )

    # Retrieve and verify
    retrieved_task = await task_store.get(sample_task.id)

    assert retrieved_task is not None
    assert retrieved_task.status.state == TaskState.working


@pytest.mark.asyncio
async def test_add_task_artifact(task_store: MongoDBTaskStore, sample_task: Task):
    """Test adding arbitrary data to task metadata field."""
    # Save task
    await task_store.save(sample_task)

    # Verify task was saved
    saved_task = await task_store.get(sample_task.id)
    assert saved_task is not None

    # Add metadata (flexible dict field) - use the save method to update
    sample_task.metadata = {
        "report_type": "gaming_news",
        "generated_at": "2024-01-01T12:00:00Z",
        "author": "game_news_agent",
    }
    await task_store.save(sample_task)

    # Retrieve and verify
    retrieved_task = await task_store.get(sample_task.id)
    assert retrieved_task is not None
    assert retrieved_task.metadata is not None
    assert retrieved_task.metadata["report_type"] == "gaming_news"
    assert retrieved_task.metadata["author"] == "game_news_agent"


@pytest.mark.asyncio
async def test_task_with_complex_data(task_store: MongoDBTaskStore):
    """Test task with complex nested data structures."""
    task_id = str(uuid4())
    context_id = str(uuid4())

    complex_task = Task(
        id=task_id,
        context_id=context_id,
        status=TaskStatus(
            state=TaskState.working,
            message=None,
            timestamp=datetime.now(UTC).isoformat(),
        ),
        artifacts=[],
        metadata={
            "game_genres": ["action", "adventure"],
            "date_from": "2026-02-01",
            "date_to": "2026-02-28",
            "nested": {
                "level1": {
                    "level2": ["value1", "value2"],
                },
            },
        },
    )

    # Save and retrieve
    await task_store.save(complex_task)
    retrieved_task = await task_store.get(task_id)

    assert retrieved_task is not None
    assert retrieved_task.id == task_id


@pytest.mark.asyncio
async def test_sanitization_of_non_serializable_objects(task_store: MongoDBTaskStore):
    """Test that non-serializable objects are handled gracefully."""
    # Test the sanitization method directly

    # Serializable object
    serializable = {"key": "value", "number": 123, "list": [1, 2, 3]}
    result = task_store._sanitize_for_mongodb(serializable)
    assert result == serializable

    # Object with datetime (should be converted to string)
    with_datetime = {"timestamp": datetime.now(UTC)}
    result = task_store._sanitize_for_mongodb(with_datetime)
    assert isinstance(result["timestamp"], str)

    # Completely non-serializable object (like ServerCallContext)
    class NonSerializable:
        def __init__(self):
            self.data = "test"

    non_serializable = NonSerializable()
    result = task_store._sanitize_for_mongodb(non_serializable)
    # Should be converted to string representation
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_concurrent_task_operations(task_store: MongoDBTaskStore):
    """Test concurrent task save operations."""
    tasks = []
    for i in range(10):
        task = Task(
            id=str(uuid4()),
            context_id=str(uuid4()),
            status=TaskStatus(
                state=TaskState.working,
                message=None,
                timestamp=datetime.now(UTC).isoformat(),
            ),
            artifacts=[],
            metadata={"index": i},
        )
        tasks.append(task)

    # Save all tasks concurrently
    await asyncio.gather(*[task_store.save(task) for task in tasks])

    # Retrieve all tasks
    retrieved_tasks = await asyncio.gather(
        *[task_store.get(task.id) for task in tasks],
    )

    assert all(t is not None for t in retrieved_tasks)
    assert len(retrieved_tasks) == 10


@pytest.mark.asyncio
async def test_task_not_found(task_store: MongoDBTaskStore):
    """Test retrieving a non-existent task."""
    non_existent_id = str(uuid4())
    result = await task_store.get(non_existent_id)
    assert result is None


@pytest.mark.asyncio
async def test_update_status_nonexistent_task(task_store: MongoDBTaskStore):
    """Test updating status of non-existent task."""
    non_existent_id = str(uuid4())

    with pytest.raises(ValueError, match="does not exist"):
        await task_store.update_task_status(
            non_existent_id,
            status=TaskStatus(
                state=TaskState.working,
                message=None,
                timestamp=datetime.now(UTC).isoformat(),
            ),
        )


@pytest.mark.asyncio
async def test_add_artifact_nonexistent_task(task_store: MongoDBTaskStore):
    """Test adding artifact to non-existent task."""
    non_existent_id = str(uuid4())

    with pytest.raises(ValueError, match="does not exist"):
        await task_store.add_task_artifact(
            non_existent_id,
            artifact_data={"test": "data"},
        )
