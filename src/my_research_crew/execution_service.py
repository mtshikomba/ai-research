"""Session-scoped background execution and cooperative cancellation state."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from threading import Event
from typing import Any, Callable
import uuid


class RunState(str, Enum):
    """Terminal and active states for one dashboard run."""

    RUNNING = "running"
    CANCELLATION_REQUESTED = "cancellation_requested"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class RunHandle:
    """Mutable session-owned handle for one background run."""

    run_id: str
    future: Future[Any]
    cancellation_requested: Event
    state: RunState = RunState.RUNNING


@dataclass(frozen=True)
class RunSnapshot:
    """Safe view of the current run state for dashboard rendering."""

    run_id: str
    state: RunState
    result: Any = None
    error: BaseException | None = None


_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="crew-run")


def start_run(
    operation: Callable[[Event], Any],
) -> RunHandle:
    """Start one background operation with a cooperative cancellation event."""
    cancellation_requested = Event()
    future = _EXECUTOR.submit(operation, cancellation_requested)
    return RunHandle(
        run_id=uuid.uuid4().hex,
        future=future,
        cancellation_requested=cancellation_requested,
    )


def request_cancellation(handle: RunHandle) -> None:
    """Request cooperative cancellation for an active run."""
    if handle.state is RunState.RUNNING:
        handle.cancellation_requested.set()
        handle.state = RunState.CANCELLATION_REQUESTED


def snapshot_run(handle: RunHandle) -> RunSnapshot:
    """Poll a run and resolve cancellation/completion races consistently."""
    if not handle.future.done():
        return RunSnapshot(handle.run_id, handle.state)

    if handle.cancellation_requested.is_set():
        handle.state = RunState.CANCELLED
        return RunSnapshot(handle.run_id, handle.state)

    try:
        result = handle.future.result()
    except BaseException as error:
        handle.state = RunState.FAILED
        return RunSnapshot(handle.run_id, handle.state, error=error)

    handle.state = RunState.COMPLETED
    return RunSnapshot(handle.run_id, handle.state, result=result)
