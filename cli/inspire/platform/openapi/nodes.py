"""Node-related helpers for the Inspire OpenAPI client."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from inspire.platform.openapi.errors import InspireAPIError, ValidationError

logger = logging.getLogger(__name__)


def list_cluster_nodes(
    api,  # noqa: ANN001
    *,
    page_num: int = 1,
    page_size: int = 10,
    resource_pool: Optional[str] = None,
) -> Dict[str, Any]:
    """Get cluster node list."""
    api._check_authentication()

    if page_num < 1:
        raise ValidationError("Page number must be at least 1")
    if page_size < 1 or page_size > 1000:
        raise ValidationError("Page size must be between 1 and 1000")

    valid_pools = ["online", "backup", "fault", "unknown"]
    if resource_pool and resource_pool not in valid_pools:
        raise ValidationError(f"Resource pool must be one of: {valid_pools}")

    payload: Dict[str, Any] = {"page_num": page_num, "page_size": page_size}

    if resource_pool:
        payload["filter"] = {"resource_pool": resource_pool}

    result = api._make_request("POST", api.endpoints.CLUSTER_NODES_LIST, payload)

    if result.get("code") == 0:
        node_count = len(result["data"].get("nodes", []))
        logger.info("🖥️  Retrieved %s nodes successfully.", node_count)
        return result

    error_msg = result.get("message", "Unknown error")
    raise InspireAPIError(f"Failed to get node list: {error_msg}")


def _openapi_path(api, suffix: str) -> str:  # noqa: ANN001
    prefix = getattr(api.endpoints, "_openapi_prefix", "/openapi/v1")
    return f"{prefix.rstrip('/')}/{suffix.lstrip('/')}"


def cluster_basic_info(api) -> Dict[str, Any]:  # noqa: ANN001
    """Get live cluster summary metadata from OpenAPI."""
    api._check_authentication()
    result = api._make_request("GET", _openapi_path(api, "cluster_basic_info"))
    if result.get("code") == 0:
        return result
    error_msg = result.get("message", "Unknown error")
    raise InspireAPIError(f"Failed to get cluster basic info: {error_msg}")


def list_node_dimension(
    api,  # noqa: ANN001
    *,
    logic_compute_group_id: str,
    workspace_id: Optional[str] = None,
    page_num: int = 1,
    page_size: int = -1,
) -> Dict[str, Any]:
    """Get live node dimensions for a compute group from OpenAPI."""
    api._check_authentication()
    if not logic_compute_group_id:
        raise ValidationError("logic_compute_group_id cannot be empty")
    if page_num < 1:
        raise ValidationError("Page number must be at least 1")
    if page_size == 0 or page_size < -1:
        raise ValidationError("Page size must be -1 or a positive integer")

    payload: Dict[str, Any] = {
        "logic_compute_group_id": logic_compute_group_id,
        "page_num": page_num,
        "page_size": page_size,
        "filter": {"logic_compute_group_id": logic_compute_group_id},
    }
    if workspace_id:
        payload["workspace_id"] = workspace_id

    result = api._make_request("POST", _openapi_path(api, "list_node_dimension"), payload)
    if result.get("code") == 0:
        return result
    error_msg = result.get("message", "Unknown error")
    raise InspireAPIError(f"Failed to list node dimensions: {error_msg}")


__all__ = ["cluster_basic_info", "list_cluster_nodes", "list_node_dimension"]
