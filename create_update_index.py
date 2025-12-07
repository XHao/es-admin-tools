import urllib.request
import urllib.error
import json
import sys
import argparse

ES_HOST = "http://localhost:9200"

def create_custom_index(index_name):
    url = f"{ES_HOST}/{index_name}"
    
    # Define custom settings and mappings
    # Example: A blog post index with custom analyzer
    payload = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
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
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Index '{index_name}' created successfully.")
            print(json.load(response))
    except urllib.error.HTTPError as e:
        print(f"Failed to create index '{index_name}': {e}")
        print(e.read().decode())
    except Exception as e:
        print(f"Error: {e}")

def update_index_mapping(index_name):
    # Add new fields 'category' and 'tags' to the existing mapping
    url = f"{ES_HOST}/{index_name}/_mapping"
    
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
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Index '{index_name}' mapping updated successfully.")
            print(json.load(response))
    except urllib.error.HTTPError as e:
        print(f"Failed to update mapping for '{index_name}': {e}")
        print(e.read().decode())
    except Exception as e:
        print(f"Error: {e}")

def update_index_settings(index_name):
    # Update dynamic settings, e.g., refresh_interval
    url = f"{ES_HOST}/{index_name}/_settings"
    
    payload = {
        "index": {
            "refresh_interval": "30s"
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Index '{index_name}' settings updated successfully.")
            print(json.load(response))
    except urllib.error.HTTPError as e:
        print(f"Failed to update settings for '{index_name}': {e}")
        print(e.read().decode())
    except Exception as e:
        print(f"Error: {e}")

def get_index_details(index_name):
    url = f"{ES_HOST}/{index_name}"
    
    try:
        with urllib.request.urlopen(url) as response:
            print(f"Details for index '{index_name}':")
            data = json.load(response)
            print(json.dumps(data, indent=4))
    except urllib.error.HTTPError as e:
        print(f"Failed to get details for index '{index_name}': {e}")
        print(e.read().decode())
    except Exception as e:
        print(f"Error: {e}")

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
