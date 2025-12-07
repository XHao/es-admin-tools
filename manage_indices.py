import urllib.request
import urllib.error
import json
import sys
import argparse

ES_HOST = "http://localhost:9200"

def list_indices(pattern="*"):
    url = f"{ES_HOST}/_cat/indices/{pattern}?v&s=index&format=json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.load(response)
            print(f"\n=== Indices ({pattern}) ===")
            if not data:
                print("No indices found.")
                return

            print(f"{'Index':<30} {'Health':<10} {'Status':<10} {'Docs Count':<12} {'Store Size':<12}")
            print("-" * 80)
            for index in data:
                print(f"{index.get('index', 'N/A'):<30} {index.get('health', 'N/A'):<10} {index.get('status', 'N/A'):<10} {index.get('docs.count', 'N/A'):<12} {index.get('store.size', 'N/A'):<12}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"No indices found matching pattern: {pattern}")
        else:
            print(f"Error listing indices: {e}")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")

def delete_index(index_name):
    url = f"{ES_HOST}/{index_name}"
    req = urllib.request.Request(url, method='DELETE')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            if data.get('acknowledged'):
                print(f"Successfully deleted index: {index_name}")
            else:
                print(f"Failed to delete index: {index_name}")
    except Exception as e:
        print(f"Error deleting index {index_name}: {e}")

def close_index(index_name):
    url = f"{ES_HOST}/{index_name}/_close"
    req = urllib.request.Request(url, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            if data.get('acknowledged'):
                print(f"Successfully closed index: {index_name}")
            else:
                print(f"Failed to close index: {index_name}")
    except Exception as e:
        print(f"Error closing index {index_name}: {e}")

def open_index(index_name):
    url = f"{ES_HOST}/{index_name}/_open"
    req = urllib.request.Request(url, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            if data.get('acknowledged'):
                print(f"Successfully opened index: {index_name}")
            else:
                print(f"Failed to open index: {index_name}")
    except Exception as e:
        print(f"Error opening index {index_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        sys.argv[1] = "-h"

    parser = argparse.ArgumentParser(description="Manage Elasticsearch Indices")
    parser.add_argument("action", choices=["list", "delete", "close", "open"], help="Action to perform")
    parser.add_argument("--index", help="Index name (required for delete, close, open)", default="*")
    
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
