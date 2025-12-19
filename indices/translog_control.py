import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import utils


def _get_translog_control_config():
    section = utils.CONFIG.get("translog_control", {})
    return section if isinstance(section, dict) else {}


def _get_mode_config(mode):
    cfg = _get_translog_control_config()
    # Backward-compatible aliases
    if mode == "enable":
        mode = "request"

    mode_cfg = cfg.get(mode, {})
    return mode_cfg if isinstance(mode_cfg, dict) else {}


def _as_bool_setting(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered
    return None


def _build_payload(mode, enabled_override=None, sync_interval_override=None, durability_override=None):
    mode_cfg = _get_mode_config(mode)

    enabled = enabled_override if enabled_override is not None else mode_cfg.get("enabled")
    durability = durability_override or mode_cfg.get("durability")
    sync_interval = sync_interval_override or mode_cfg.get("sync_interval")

    payload = {}
    enabled_setting = _as_bool_setting(enabled)
    if enabled_setting is not None:
        payload["index.translog.enabled"] = enabled_setting
    if durability:
        payload["index.translog.durability"] = durability
    if sync_interval:
        payload["index.translog.sync_interval"] = sync_interval

    # Indices put settings accepts flat settings keys.
    return payload


def set_translog_mode(index_name, mode, *, enabled=None, sync_interval=None, durability=None):
    """Set translog-related index settings.

    In Elasticsearch 8, translog behavior is controlled by index settings.
    The key switch for enable/disable is `index.translog.enabled`.

    Args:
        index_name: index name
        mode: 'enable' or 'disable'
        enabled: optional override for index.translog.enabled
        sync_interval: optional override for index.translog.sync_interval
        durability: optional override for index.translog.durability
    """
    if mode not in {"request", "async", "disable", "enable"}:
        raise ValueError("mode must be one of: request, async, disable")

    # Normalize legacy alias
    if mode == "enable":
        mode = "request"

    payload = _build_payload(
        mode,
        enabled_override=enabled,
        sync_interval_override=sync_interval,
        durability_override=durability,
    )
    if not payload:
        return None

    return utils.make_request(f"{index_name}/_settings", method="PUT", data=payload)


def get_translog_settings(index_name):
    # Filter to just translog settings for readability
    endpoint = f"{index_name}/_settings?filter_path=*.settings.index.translog.*"
    return utils.make_request(endpoint)


def pretty_print(data):
    print(json.dumps(data, indent=2, sort_keys=True))
