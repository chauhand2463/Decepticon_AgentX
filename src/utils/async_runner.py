import asyncio
import threading
from typing import Coroutine, Any

_shared_loop = None
_loop_thread = None


def _start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Runs the event loop forever inside the background thread."""
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()


def get_shared_loop() -> asyncio.AbstractEventLoop:
    """Gets or establishes the shared background event loop."""
    global _shared_loop, _loop_thread
    if _shared_loop is None:
        _shared_loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(
            target=_start_background_loop,
            args=(_shared_loop,),
            daemon=True,
            name="DecepticonAsyncRunner",
        )
        _loop_thread.start()
    return _shared_loop


def run_async(coro: Coroutine) -> Any:
    """
    Submit a coroutine to the background event loop and block until completion.
    Safe for Streamlit which creates/destroys threads.
    """
    loop = get_shared_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    # Block calling thread until the coroutine is finished
    return future.result()
