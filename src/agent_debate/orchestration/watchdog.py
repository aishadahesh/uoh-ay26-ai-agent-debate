"""Watchdog helpers for child processes."""

from __future__ import annotations

from multiprocessing import Process


class Watchdog:
    """Detects dead child processes and timeout failures."""

    def __init__(self, response_timeout: float, restart_attempts: int) -> None:
        self.response_timeout = response_timeout
        self.restart_attempts = restart_attempts

    def ensure_alive(self, role: str, process: Process) -> None:
        """Fail clearly if a child process has died."""

        if not process.is_alive():
            raise RuntimeError(f"{role} process is not alive")
