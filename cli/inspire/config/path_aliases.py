"""Remote path alias helpers for project config and notebook commands."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from inspire.config.models import CONFIG_FILENAME, PROJECT_CONFIG_DIR, ConfigError
from inspire.config.toml import _find_project_config, _load_toml

_ALIAS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
PATH_ALIASES_SECTION = "path_aliases"


def normalize_path_alias_map(raw_value: Any) -> dict[str, str]:
    """Normalize a TOML ``[path_aliases]`` table into ``alias -> path``."""
    if not isinstance(raw_value, dict):
        return {}

    result: dict[str, str] = {}

    def _walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                child = str(child_key or "").strip()
                if not child:
                    continue
                next_prefix = f"{prefix}.{child}" if prefix else child
                _walk(next_prefix, child_value)
            return

        alias = prefix.strip()
        path = str(value or "").strip()
        if not alias or not path:
            return
        result[alias] = path

    _walk("", raw_value)
    return result


def validate_path_alias(alias: str) -> str:
    value = str(alias or "").strip()
    if not value:
        raise ConfigError("Path alias cannot be empty.")
    if value == "as":
        raise ConfigError("Path alias cannot be 'as'.")
    if not _ALIAS_RE.match(value):
        raise ConfigError(
            "Invalid path alias. Use letters, digits, '.', '_' or '-', "
            "and start with a letter or digit."
        )
    return value


def validate_remote_alias_path(path: str) -> str:
    value = str(path or "").strip()
    if not value:
        raise ConfigError("Remote path cannot be empty.")
    if not value.startswith("/"):
        raise ConfigError("Remote path aliases must point to an absolute remote path.")
    return value


def _join_remote_path(base: str, suffix: str) -> str:
    base = str(base or "").rstrip("/")
    suffix = str(suffix or "").strip()
    if not suffix:
        return base or "/"
    suffix = suffix.lstrip("/")
    if not suffix:
        return base or "/"
    return f"{base}/{suffix}"


def resolve_remote_path_alias(
    value: str,
    aliases: dict[str, str] | None,
    *,
    require_absolute_or_alias: bool = False,
) -> tuple[str, bool]:
    """Resolve exact, ``alias:child`` or ``alias/child`` remote path aliases.

    Returns ``(resolved_path, used_alias)``. Unknown relative values are
    preserved for SCP compatibility unless ``require_absolute_or_alias`` is set.
    """
    text = str(value or "").strip()
    alias_map = aliases or {}
    if not text:
        return text, False

    if text in alias_map:
        return alias_map[text], True

    if ":" in text:
        alias, suffix = text.split(":", 1)
        alias = alias.strip()
        if alias in alias_map:
            return _join_remote_path(alias_map[alias], suffix), True
        if require_absolute_or_alias and alias:
            raise ConfigError(f"Unknown path alias '{alias}'.")

    for alias in sorted(alias_map, key=len, reverse=True):
        prefix = f"{alias}/"
        if text.startswith(prefix):
            return _join_remote_path(alias_map[alias], text[len(prefix):]), True

    if require_absolute_or_alias and not text.startswith("/"):
        raise ConfigError(
            f"Unknown path alias or relative remote path: '{text}'. "
            "Use an absolute path or define it with `inspire notebook set-path`."
        )

    return text, False


def resolve_remote_cwd(*, cwd: str | None, target_dir: str | None, aliases: dict[str, str]) -> str:
    raw = str(cwd or target_dir or "").strip()
    if not raw:
        raise ConfigError("Missing remote working directory.")
    resolved, _ = resolve_remote_path_alias(
        raw,
        aliases,
        require_absolute_or_alias=True,
    )
    return resolved


def project_path_alias_config_path() -> Path:
    return _find_project_config() or Path.cwd() / PROJECT_CONFIG_DIR / CONFIG_FILENAME


def write_project_path_alias(*, alias: str, remote_path: str) -> Path:
    """Write one path alias to the nearest project config and return its path."""
    alias = validate_path_alias(alias)
    remote_path = validate_remote_alias_path(remote_path)

    config_path = project_path_alias_config_path()
    if config_path.exists():
        data = _load_toml(config_path)
    else:
        data = {}

    section = data.get(PATH_ALIASES_SECTION)
    if not isinstance(section, dict):
        section = {}
        data[PATH_ALIASES_SECTION] = section
    section[alias] = remote_path

    from inspire.cli.commands.init.toml_helpers import _toml_dumps

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(_toml_dumps(data), encoding="utf-8")
    return config_path


__all__ = [
    "PATH_ALIASES_SECTION",
    "normalize_path_alias_map",
    "project_path_alias_config_path",
    "resolve_remote_cwd",
    "resolve_remote_path_alias",
    "validate_path_alias",
    "validate_remote_alias_path",
    "write_project_path_alias",
]
