"""Centralized dependencies for job-related CLI code.

Tests can patch ``time.time`` here and the patch will be observed across
all job command modules.

The previous ``JobCache`` / ``fetch_remote_log_via_bridge`` attributes
were removed when the local job cache and the deprecated
GitHub-workflow log fetcher were dropped — both flows are now
SSH-tunnel-only.
"""

from __future__ import annotations

import time

__all__ = ["time"]
