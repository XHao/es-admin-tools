import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import json
import argparse

def create_custom_index(index_name):
    # Define custom settings and mappings
    # Example: A blog post index with custom analyzer
    shards = utils.CONFIG.get("default_shards", 2)
    replicas = utils.CONFIG.get("default_replicas", 1)
    
    payload = {
        "settings": {
            "number_of_shards": shards,
            "number_of_replicas": replicas,
            "analysis": {
                "analyzer": {
                    "my_custom_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "my_custom_analyzer"
                },
                "content": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "created_at": {
                    "type": "date"
                },
                "views": {
                    "type": "integer"
                }
            }
        }
    }
    
    data = utils.make_request(index_name, method='PUT', data=payload)
    if data and 'acknowledged' in data:
        print(f"Index '{index_name}' created successfully.")
        print(json.dumps(data, indent=4))
    else:
        print(f"Failed to create index '{index_name}'.")

def update_index_mapping(index_name):
    # Add new fields 'category' and 'tags' to the existing mapping
    payload = {
        "properties": {
            "category": {
                "type": "keyword"
            },
            "tags": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            }
        }
    }
    
    data = utils.make_request(f"{index_name}/_mapping", method='PUT', data=payload)
    if data and 'acknowledged' in data:
        print(f"Index '{index_name}' mapping updated successfully.")
        print(json.dumps(data, indent=4))
    else:
        print(f"Failed to update mapping for '{index_name}'.")

def update_index_settings(index_name):
    # Update dynamic settings, e.g., refresh_interval
    refresh_interval = utils.CONFIG.get("default_refresh_interval", "30s")
    payload = {
        "index": {
            "refresh_interval": refresh_interval
        }
    }
    
    data = utils.make_request(f"{index_name}/_settings", method='PUT', data=payload)
    if data and 'acknowledged' in data:
        print(f"Index '{index_name}' settings updated successfully.")
        print(json.dumps(data, indent=4))
    else:
        print(f"Failed to update settings for '{index_name}'.")

def get_index_details(index_name):
    data = utils.make_request(index_name)
    if data:
        print(f"Details for index '{index_name}':")
        print(json.dumps(data, indent=4))
    else:
        print(f"Failed to get details for index '{index_name}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create and Update Custom Index")
    parser.add_argument("action", choices=["create", "update_mapping", "update_settings", "details"], help="Action to perform")
    parser.add_argument("--index", default="my-custom-index", help="Index name (default: my-custom-index)")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_custom_index(args.index)
    elif args.action == "update_mapping":
        update_index_mapping(args.index)
    elif args.action == "update_settings":
        update_index_settings(args.index)
    elif args.action == "details":
        get_index_details(args.index)
