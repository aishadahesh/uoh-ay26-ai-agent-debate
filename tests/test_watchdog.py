from multiprocessing import Process

import pytest

from agent_debate.orchestration.watchdog import Watchdog


def test_watchdog_detects_dead_process() -> None:
    process = Process(target=lambda: None)
    watchdog = Watchdog(response_timeout=0.1, restart_attempts=0)
    with pytest.raises(RuntimeError, match="not alive"):
        watchdog.ensure_alive("pro", process)
