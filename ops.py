#!/usr/bin/env python3
import argparse
import sys
import os

# Ensure the current directory is in sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from monitor import check_cluster_health, cluster_diagnostics
from indices import manage_indices, create_update_index
from ingest import ingest_logs
from search import search_index

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
    elif args.action == "delete":
        if args.name == "*":
            print("Error: Wildcard '*' not allowed for delete via this tool for safety.")
            return
        confirm = input(f"Are you sure you want to DELETE index '{args.name}'? (y/n): ")
        if confirm.lower() == 'y':
            manage_indices.delete_index(args.name)
    elif args.action == "close":
        manage_indices.close_index(args.name)
    elif args.action == "open":
        manage_indices.open_index(args.name)
    elif args.action == "create":
        create_update_index.create_custom_index(args.name)
    elif args.action == "details":
        create_update_index.get_index_details(args.name)
    elif args.action == "update-mapping":
        create_update_index.update_index_mapping(args.name)
    elif args.action == "update-settings":
        create_update_index.update_index_settings(args.name)

def handle_ingest(args):
    ingest_logs.ingest_logs(args.index)

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

    # Indices Command
    indices_parser = subparsers.add_parser("indices", help="Manage indices (list, delete, create, etc.)")
    indices_parser.add_argument("action", choices=[
        "list", "delete", "close", "open", 
        "create", "details", "update-mapping", "update-settings"
    ], help="Action to perform on indices")
    indices_parser.add_argument("--name", "--index", dest="name", default="*", help="Index name or pattern (default: *)")
    indices_parser.add_argument("--pattern", default="*", help="Index pattern for listing (default: *)")
    indices_parser.set_defaults(func=handle_indices)

    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest sample logs")
    ingest_parser.add_argument("--index", default="logs-sample", help="Target index name (default: logs-sample)")
    ingest_parser.set_defaults(func=handle_ingest)

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search an index")
    search_parser.add_argument("--index", required=True, help="Index to search")
    search_parser.add_argument("--query", help="Query string (e.g. 'field:value')")
    search_parser.add_argument("--size", type=int, default=10, help="Number of results")
    search_parser.set_defaults(func=handle_search)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
