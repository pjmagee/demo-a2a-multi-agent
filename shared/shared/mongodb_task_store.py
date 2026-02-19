"""MongoDB-based TaskStore implementation for A2A agents."""

import logging
from datetime import UTC, datetime
from typing import Any

from a2a.server.tasks.task_store import TaskStore
from a2a.types import Task, TaskState, TaskStatus
from motor.motor_asyncio import (  # type: ignore[import-not-found]
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
)
from pymongo import ASCENDING  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class MongoDBTaskStore(TaskStore):
    """MongoDB-backed task persistence for A2A agents.

    Stores tasks with full state tracking, artifact updates, and metadata.
    Designed to work with Aspire-orchestrated MongoDB containers.
    """

    def __init__(
        self,
        connection_string: str,
        database_name: str = "a2a_tasks",
        collection_name: str = "tasks",
    ) -> None:
        """Initialize MongoDB task store.

        Args:
            connection_string: MongoDB connection string
            database_name: Database name for tasks
            collection_name: Collection name for tasks

        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name

        self.client: AsyncIOMotorClient[Any] | None = None
        self.collection: AsyncIOMotorCollection[Any] | None = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure MongoDB client is initialized and indexes are created."""
        if self._initialized:
            return

        logger.info(
            "Initializing MongoDB TaskStore: %s.%s",
            self.database_name,
            self.collection_name,
        )

        # Create client and get collection
        self.client = AsyncIOMotorClient(self.connection_string)
        if self.client is None:
            msg = "Failed to create MongoDB client"
            raise RuntimeError(msg)

        db = self.client[self.database_name]
        self.collection = db[self.collection_name]

        # Type narrowing for type checker
        if self.collection is None:
            msg = "Failed to initialize MongoDB collection"
            raise RuntimeError(msg)

        # Create indexes for efficient queries
        await self.collection.create_index("task_id", unique=True)
        await self.collection.create_index("context_id")
        await self.collection.create_index("status")
        await self.collection.create_index([("created_at", ASCENDING)])
        await self.collection.create_index([("updated_at", ASCENDING)])

        self._initialized = True
        logger.info("MongoDB TaskStore initialized successfully")

    async def get(self, task_id: str) -> Task | None:
        """Retrieve a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task object if found, None otherwise

        """
        await self._ensure_initialized()
        if self.collection is None:
            msg = "MongoDB collection not initialized"
            raise RuntimeError(msg)

        task_doc = await self.collection.find_one({"task_id": task_id})
        if not task_doc:
            logger.debug("Task not found: %s", task_id)
            return None

        return self._document_to_task(task_doc)

    async def save(self, task: Task) -> None:
        """Save (create or update) a task in MongoDB.

        Args:
            task: Task object to persist

        """
        await self._ensure_initialized()
        if self.collection is None:
            msg = "MongoDB collection not initialized"
            raise RuntimeError(msg)

        task_doc = self._task_to_document(task)
        now = datetime.now(UTC)
        
        # Check if task exists
        existing = await self.collection.find_one({"task_id": task.id})
        
        if existing:
            # Update existing task
            task_doc["updated_at"] = now
            await self.collection.replace_one(
                {"task_id": task.id},
                task_doc,
            )
            logger.info("Updated task: %s (context: %s)", task.id, task.context_id)
        else:
            # Create new task
            task_doc["created_at"] = now
            task_doc["updated_at"] = now
            await self.collection.insert_one(task_doc)
            logger.info("Created task: %s (context: %s)", task.id, task.context_id)

    async def delete(self, task_id: str) -> None:
        """Delete a task from MongoDB.

        Args:
            task_id: Task identifier

        """
        await self._ensure_initialized()
        if self.collection is None:
            msg = "MongoDB collection not initialized"
            raise RuntimeError(msg)

        result = await self.collection.delete_one({"task_id": task_id})
        if result.deleted_count > 0:
            logger.info("Deleted task: %s", task_id)
        else:
            logger.warning("Task not found for deletion: %s", task_id)

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB TaskStore connection closed")
            self._initialized = False

    def _task_to_document(self, task: Task) -> dict[str, Any]:
        """Convert Task object to MongoDB document.

        Args:
            task: Task object

        Returns:
            MongoDB document dict

        """
        # Use Pydantic's model_dump for serialization
        doc = task.model_dump(mode="json")

        # Rename 'id' to 'task_id' for MongoDB (avoid _id conflicts)
        doc["task_id"] = doc.pop("id")

        return doc

    def _document_to_task(self, doc: dict[str, Any]) -> Task:
        """Convert MongoDB document to Task object.

        Args:
            doc: MongoDB document

        Returns:
            Task object

        """
        # Rename task_id back to id
        doc["id"] = doc.pop("task_id")

        # Remove MongoDB metadata
        doc.pop("_id", None)
        doc.pop("created_at", None)
        doc.pop("updated_at", None)

        # Reconstruct Task using Pydantic
        return Task(**doc)

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        state: TaskState | None = None,
    ) -> None:
        """Update task status and optionally state.

        Args:
            task_id: Task identifier
            status: New task status (TaskStatus model)
            state: Optional task state update (enum)

        """
        await self._ensure_initialized()
        if self.collection is None:
            msg = "MongoDB collection not initialized"
            raise RuntimeError(msg)

        update_doc: dict[str, Any] = {
            "status": status.model_dump(mode="json"),
            "updated_at": datetime.now(UTC),
        }

        if state:
            # TaskState is an enum, use .value
            update_doc["state"] = state.value

        result = await self.collection.update_one(
            {"task_id": task_id},
            {"$set": update_doc},
        )

        if result.matched_count == 0:
            msg = f"Task {task_id} does not exist"
            logger.error("Task %s not found for status update", task_id)
            raise ValueError(msg)

        logger.info("Updated task status: %s -> %s", task_id, status)

    async def add_task_artifact(
        self,
        task_id: str,
        artifact_data: dict[str, Any],
    ) -> None:
        """Add an artifact to a task's artifact list.

        Args:
            task_id: Task identifier
            artifact_data: Artifact data dict

        """
        await self._ensure_initialized()
        if self.collection is None:
            msg = "MongoDB collection not initialized"
            raise RuntimeError(msg)

        result = await self.collection.update_one(
            {"task_id": task_id},
            {
                "$push": {"artifacts": artifact_data},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )

        if result.matched_count == 0:
            msg = f"Task {task_id} does not exist"
            logger.error("Task %s not found for artifact addition", task_id)
            raise ValueError(msg)

        logger.info("Added artifact to task: %s", task_id)
