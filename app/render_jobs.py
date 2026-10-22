"""Thread-safe in-process render jobs with real progress and cancellation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import threading
import time

from .job_errors import JobCancelled


TERMINAL_STATES = {"complete", "failed", "cancelled"}


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


class RenderJobManager:
    """Own render futures and expose a JSON-safe view of each job."""

    def __init__(self, *, max_workers=1, inline=False, retention_seconds=24 * 60 * 60):
        self._executor = ThreadPoolExecutor(max_workers=max(1, int(max_workers)),
                                            thread_name_prefix="quran-render")
        self._inline = bool(inline)
        self._retention_seconds = int(retention_seconds)
        self._lock = threading.RLock()
        self._jobs = {}

    def submit(self, job_id, worker):
        """Register a job and run worker(update, cancel_event) in the pool."""
        self._purge_expired()
        now = time.monotonic()
        record = {
            "id": job_id,
            "status": "queued",
            "phase": "queued",
            "progress": 0,
            "message": "Waiting for an available render slot.",
            "error": None,
            "result": None,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "_created_monotonic": now,
            "_started_monotonic": None,
            "_finished_monotonic": None,
            "_cancel": threading.Event(),
            "_future": None,
        }
        with self._lock:
            self._jobs[job_id] = record

        if self._inline:
            self._run(job_id, worker)
        else:
            future = self._executor.submit(self._run, job_id, worker)
            with self._lock:
                record["_future"] = future
        return self.get(job_id)

    def _run(self, job_id, worker):
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record["_cancel"].is_set():
                if record is not None:
                    self._finish_cancelled(record)
                return
            record.update(status="running", phase="starting", message="Preparing the render.",
                          updated_at=_utc_now(), _started_monotonic=time.monotonic())
            cancel_event = record["_cancel"]

        def update(*, progress=None, phase=None, message=None, render_speed_fps=None,
                   estimated_remaining_seconds=None):
            with self._lock:
                current = self._jobs.get(job_id)
                if current is None or current["status"] in TERMINAL_STATES:
                    return
                if progress is not None:
                    current["progress"] = max(current["progress"],
                                               min(99, max(0, int(round(progress)))))
                if phase is not None:
                    current["phase"] = str(phase)
                if message is not None:
                    current["message"] = str(message)
                if render_speed_fps is not None:
                    current["render_speed_fps"] = round(max(0.0, float(render_speed_fps)), 2)
                if estimated_remaining_seconds is not None:
                    current["estimated_remaining_seconds"] = max(0, int(estimated_remaining_seconds))
                current["updated_at"] = _utc_now()

        try:
            result = worker(update, cancel_event)
            with self._lock:
                current = self._jobs.get(job_id)
                if current is not None and current["status"] not in TERMINAL_STATES:
                    current.update(status="complete", phase="complete", progress=100,
                                   message="Video is ready to preview and download.",
                                   result=result, error=None, updated_at=_utc_now(),
                                   _finished_monotonic=time.monotonic())
        except JobCancelled:
            with self._lock:
                current = self._jobs.get(job_id)
                if current is not None:
                    self._finish_cancelled(current)
        except Exception as exc:
            with self._lock:
                current = self._jobs.get(job_id)
                if current is not None:
                    current.update(status="failed", phase="failed", error=str(exc),
                                   message="Rendering failed. Review the error and try again.",
                                   updated_at=_utc_now(), _finished_monotonic=time.monotonic())

    @staticmethod
    def _finish_cancelled(record):
        record.update(status="cancelled", phase="cancelled", message="Render cancelled.",
                      updated_at=_utc_now(), _finished_monotonic=time.monotonic())

    def get(self, job_id):
        self._purge_expired()
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            snapshot = {key: value for key, value in record.items() if not key.startswith("_")}
            started = record.get("_started_monotonic")
            if started is not None and record["status"] not in TERMINAL_STATES:
                snapshot["elapsed_seconds"] = round(max(0.0, time.monotonic() - started), 1)
            return snapshot

    def cancel(self, job_id):
        """Request cooperative cancellation; return the current public snapshot."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            if record["status"] in TERMINAL_STATES:
                return {key: value for key, value in record.items() if not key.startswith("_")}
            record["_cancel"].set()
            future = record.get("_future")
            if future is not None and future.cancel():
                self._finish_cancelled(record)
            else:
                record["message"] = "Cancellation requested. Stopping at the next safe render boundary."
                record["updated_at"] = _utc_now()
            return {key: value for key, value in record.items() if not key.startswith("_")}

    def _purge_expired(self):
        cutoff = time.monotonic() - self._retention_seconds
        with self._lock:
            expired = [job_id for job_id, record in self._jobs.items()
                       if record["status"] in TERMINAL_STATES
                       and record["_finished_monotonic"] is not None
                       and record["_finished_monotonic"] < cutoff]
            for job_id in expired:
                del self._jobs[job_id]

    def shutdown(self, *, wait=False):
        self._executor.shutdown(wait=wait, cancel_futures=True)
