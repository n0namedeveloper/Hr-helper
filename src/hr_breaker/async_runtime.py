# src/hr_breaker/async_runtime.py
import asyncio
import threading

_loop = asyncio.new_event_loop()

def _run_loop():
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

_thread = threading.Thread(target=_run_loop, daemon=True)
_thread.start()

def run_sync(coro):
    """Run coroutine in the global event loop and wait for result."""
    fut = asyncio.run_coroutine_threadsafe(coro, _loop)
    return fut.result()
