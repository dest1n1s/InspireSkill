"""Centralized dependencies for job-related CLI code.

Tests can patch ``time.time`` here and the patch will be observed across
all job command modules.

The previous local-cache and GitHub-workflow log fetcher hooks were
dropped. Job commands now use live platform APIs for job state and the
SSH tunnel path for logs.
"""

from __future__ import annotations

import time

__all__ = ["time"]
