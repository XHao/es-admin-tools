#!/usr/bin/env python3
import argparse
import sys
import os

# Ensure the current directory is in sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from monitor import check_cluster_health, cluster_diagnostics
from indices import manage_indices, create_update_index
from indices import translog_control
from ingest import ingest_logs
from search import search_index
import utils


def _coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def handle_health(args):
    check_cluster_health.get_cluster_health()
    check_cluster_health.get_nodes_info()

def handle_diagnose(args):
    cluster_diagnostics.run_diagnostics()

def handle_search(args):
    search_index.search_index(args.index, args.query, args.size)

def handle_indices(args):
    if args.action == "list":
        manage_indices.list_indices(args.pattern)
        return

    default_index_name = utils.CONFIG.get("default_ingest_index", "logs-sample")
    resolved_name = args.name if args.name not in (None, "") else None

    if args.action in {"create", "details", "update-mapping", "update-settings"}:
        if resolved_name in (None, "*"):
            resolved_name = default_index_name
    else:
        # Safety: destructive/operational actions require an explicit index name.
        if resolved_name in (None, "*"):
            print("Error: Please specify --name for this action (wildcards not allowed).")
            return

    if args.action == "delete":
        confirm = input(f"Are you sure you want to DELETE index '{resolved_name}'? (y/n): ")
        if confirm.lower() == 'y':
            manage_indices.delete_index(resolved_name)
    elif args.action == "close":
        manage_indices.close_index(resolved_name)
    elif args.action == "open":
        manage_indices.open_index(resolved_name)
    elif args.action == "create":
        create_update_index.create_custom_index(resolved_name)
    elif args.action == "details":
        create_update_index.get_index_details(resolved_name)
    elif args.action == "update-mapping":
        create_update_index.update_index_mapping(resolved_name)
    elif args.action == "update-settings":
        create_update_index.update_index_settings(resolved_name)

def handle_ingest(args):
    ingest_logs.ingest_logs(args.index)


def handle_translog(args):
    # Node-level overview
    cluster_diagnostics.check_translog_stats()

    # Optional: shard-level breakdown for a specific index
    if args.index:
        cluster_diagnostics.check_index_translog(args.index)


def handle_translog_mode(args):
    index_name = args.index or utils.CONFIG.get("default_ingest_index", "logs-sample")

    if args.mode == "disable" and not args.yes:
        print("WARNING: This sets index.translog.enabled=false (affects durability/recovery).")
        confirm = input(f"Proceed to set translog mode to '{args.mode}' for index '{index_name}'? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    # Translate the 3 modes into explicit settings. Config.json provides defaults.
    # request  -> enabled=true, durability=request
    # async    -> enabled=true, durability=async
    # disable  -> enabled=false
    enabled_override = args.enabled
    durability_override = args.durability
    sync_interval_override = args.sync_interval

    if args.mode in {"request", "async"}:
        enabled_override = enabled_override or "true"
        durability_override = durability_override or args.mode
    elif args.mode == "disable":
        enabled_override = enabled_override or "false"

    result = translog_control.set_translog_mode(
        index_name,
        args.mode,
        enabled=enabled_override,
        sync_interval=sync_interval_override,
        durability=durability_override,
    )

    if result and result.get('acknowledged'):
        print(f"Translog mode '{args.mode}' applied to index '{index_name}'.")
    else:
        print(f"Failed to apply translog mode '{args.mode}' to index '{index_name}'.")
        if result:
            print(result)
        return

    current = translog_control.get_translog_settings(index_name)
    if current:
        print("Current translog settings:")
        translog_control.pretty_print(current)

def main():
    parser = argparse.ArgumentParser(description="Elasticsearch Daily Operations CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.required = True

    # Health Command
    health_parser = subparsers.add_parser("health", help="Check cluster health and nodes info")
    health_parser.set_defaults(func=handle_health)

    # Diagnose Command
    diagnose_parser = subparsers.add_parser("diagnose", help="Run comprehensive cluster diagnostics")
    diagnose_parser.set_defaults(func=handle_diagnose)

    # Translog Command
    translog_parser = subparsers.add_parser(
        "translog",
        help="Check translog stats (Uncommitted Ops is about Lucene flush/commit, not fsync timing)",
    )
    translog_parser.add_argument("--index", help="Optional index name for shard-level translog stats")
    translog_parser.set_defaults(func=handle_translog)

    # Translog Mode Command
    translog_mode_parser = subparsers.add_parser(
        "translog-mode",
        help="Enable/disable translog for an index (index.translog.enabled) and optionally set durability/sync_interval",
    )
    translog_mode_parser.add_argument(
        "mode",
        choices=["request", "async", "disable"],
        help="Mode to apply: request|async (enabled), or disable",
    )
    translog_mode_parser.add_argument(
        "--index",
        help="Target index name (default from config.json: default_ingest_index)",
    )
    translog_mode_parser.add_argument(
        "--enabled",
        choices=["true", "false"],
        help="Override index.translog.enabled (default from config.json translog_control.*.enabled)",
    )
    translog_mode_parser.add_argument(
        "--durability",
        choices=["request", "async"],
        help="Override durability (default from config.json translog_control.*.durability)",
    )
    translog_mode_parser.add_argument(
        "--sync-interval",
        help="Override index.translog.sync_interval (default from config.json translog_control.*.sync_interval)",
    )
    translog_mode_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt for disable",
    )
    translog_mode_parser.set_defaults(func=handle_translog_mode)

    # Indices Command
    indices_parser = subparsers.add_parser("indices", help="Manage indices (list, delete, create, etc.)")
    indices_parser.add_argument("action", choices=[
        "list", "delete", "close", "open", 
        "create", "details", "update-mapping", "update-settings"
    ], help="Action to perform on indices")
    indices_parser.add_argument("--name", "--index", dest="name", default=None, help="Index name")
    indices_parser.add_argument(
        "--pattern",
        default=utils.CONFIG.get("default_index_pattern", "*"),
        help="Index pattern for listing (default from config.json)",
    )
    indices_parser.set_defaults(func=handle_indices)

    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest sample logs")
    ingest_parser.add_argument(
        "--index",
        default=utils.CONFIG.get("default_ingest_index", "logs-sample"),
        help="Target index name (default from config.json)",
    )
    ingest_parser.set_defaults(func=handle_ingest)

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search an index")
    search_parser.add_argument("--index", required=True, help="Index to search")
    search_parser.add_argument("--query", help="Query string (e.g. 'field:value')")
    search_parser.add_argument(
        "--size",
        type=int,
        default=_coerce_int(utils.CONFIG.get("default_search_size", 10), 10),
        help="Number of results (default from config.json)",
    )
    search_parser.set_defaults(func=handle_search)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
