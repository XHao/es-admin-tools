import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import argparse

DEFAULT_PATTERN = utils.CONFIG.get("default_index_pattern", "*")

def list_indices(pattern=None):
    if pattern is None:
        pattern = DEFAULT_PATTERN
    data = utils.make_request(f"_cat/indices/{pattern}?v&s=index&format=json")
    print(f"\n=== Indices ({pattern}) ===")
    if not data:
        print("No indices found.")
        return

    print(f"{'Index':<30} {'Health':<10} {'Status':<10} {'Docs Count':<12} {'Store Size':<12}")
    print("-" * 80)
    for index in data:
        print(f"{index.get('index', 'N/A'):<30} {index.get('health', 'N/A'):<10} {index.get('status', 'N/A'):<10} {index.get('docs.count', 'N/A'):<12} {index.get('store.size', 'N/A'):<12}")

def delete_index(index_name):
    data = utils.make_request(index_name, method='DELETE')
    if data and data.get('acknowledged'):
        print(f"Successfully deleted index: {index_name}")
    else:
        print(f"Failed to delete index: {index_name}")

def close_index(index_name):
    data = utils.make_request(f"{index_name}/_close", method='POST')
    if data and data.get('acknowledged'):
        print(f"Successfully closed index: {index_name}")
    else:
        print(f"Failed to close index: {index_name}")

def open_index(index_name):
    data = utils.make_request(f"{index_name}/_open", method='POST')
    if data and data.get('acknowledged'):
        print(f"Successfully opened index: {index_name}")
    else:
        print(f"Failed to open index: {index_name}")

if __name__ == "__main__":
    # Handle legacy "help" argument if passed directly
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        sys.argv[1] = "-h"

    parser = argparse.ArgumentParser(description="Manage Elasticsearch Indices")
    parser.add_argument("action", choices=["list", "delete", "close", "open"], help="Action to perform")
    parser.add_argument(
        "--index",
        help="Index pattern for list, or index name for delete/close/open (default from config.json)",
        default=DEFAULT_PATTERN,
    )
    
    args = parser.parse_args()

    if args.action == "list":
        list_indices(args.index)
    elif args.action in ["delete", "close", "open"]:
        if args.index == "*":
            print("Error: Please specify a specific index name for this action (wildcards not recommended for safety).")
        else:
            if args.action == "delete":
                confirm = input(f"Are you sure you want to DELETE index '{args.index}'? (y/n): ")
                if confirm.lower() == 'y':
                    delete_index(args.index)
            elif args.action == "close":
                close_index(args.index)
            elif args.action == "open":
                open_index(args.index)
