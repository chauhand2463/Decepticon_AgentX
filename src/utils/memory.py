import logging
from typing import Optional
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

logger = logging.getLogger(__name__)

_checkpointer: Optional[InMemorySaver] = None
_store: Optional[InMemoryStore] = None


def get_checkpointer() -> InMemorySaver:

    global _checkpointer

    if _checkpointer is None:
        _checkpointer = InMemorySaver()
        logger.info("InMemorySaver checkpointer initialized")

    return _checkpointer


def get_store() -> InMemoryStore:

    global _store

    if _store is None:
        _store = InMemoryStore()
        logger.info("InMemoryStore initialized")

    return _store


def reset_persistence():

    global _checkpointer, _store

    _checkpointer = None
    _store = None
    logger.info("Persistence instances reset")


def get_persistence_status() -> dict:

    return {
        "checkpointer_initialized": _checkpointer is not None,
        "store_initialized": _store is not None,
        "checkpointer_type": type(_checkpointer).__name__ if _checkpointer else None,
        "store_type": type(_store).__name__ if _store else None,
    }


def create_thread_config(user_id: str, conversation_id: Optional[str] = None) -> dict:

    thread_id = f"user_{user_id}"
    if conversation_id:
        thread_id += f"_conv_{conversation_id}"

    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": "main"}}

    logger.debug(f"Created thread config: {config}")
    return config


def create_memory_namespace(user_id: str, namespace_type: str = "memories") -> tuple:

    return (namespace_type, user_id)


def get_debug_info() -> dict:

    status = get_persistence_status()

    debug_info = status.copy()

    if _checkpointer:
        debug_info["checkpointer_class"] = str(type(_checkpointer))

    if _store:
        debug_info["store_class"] = str(type(_store))

        try:
            debug_info["store_has_index"] = hasattr(_store, "index")
        except Exception:
            debug_info["store_has_index"] = False

    return debug_info
