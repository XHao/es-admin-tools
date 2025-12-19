import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import json
import argparse


def _deep_merge(base, override):
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_create_update_index_config():
    section = utils.CONFIG.get("create_update_index", {})
    return section if isinstance(section, dict) else {}


def _default_create_fragment():
    return {
        "analysis": {
            "analyzer": {
                "my_custom_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop"],
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {"type": "text", "analyzer": "my_custom_analyzer"},
                "content": {"type": "text", "analyzer": "standard"},
                "created_at": {"type": "date"},
                "views": {"type": "integer"},
            }
        },
    }


def _default_update_mapping_payload():
    return {
        "properties": {
            "category": {"type": "keyword"},
            "tags": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
        }
    }


def _default_update_settings_payload():
    refresh_interval = utils.CONFIG.get("default_refresh_interval", "30s")
    return {"index": {"refresh_interval": refresh_interval}}

def create_custom_index(index_name):
    shards = _coerce_int(utils.CONFIG.get("default_shards", 2), 2)
    replicas = _coerce_int(utils.CONFIG.get("default_replicas", 1), 1)

    cfg = _get_create_update_index_config()
    create_fragment = _deep_merge(_default_create_fragment(), cfg.get("create", {}))

    settings = {
        "number_of_shards": shards,
        "number_of_replicas": replicas,
    }
    if isinstance(create_fragment.get("analysis"), dict) and create_fragment["analysis"]:
        settings["analysis"] = create_fragment["analysis"]

    payload = {
        "settings": settings,
        "mappings": create_fragment.get("mappings", {}),
    }
    
    data = utils.make_request(index_name, method='PUT', data=payload)
    if data and 'acknowledged' in data:
        print(f"Index '{index_name}' created successfully.")
        print(json.dumps(data, indent=4))
    else:
        print(f"Failed to create index '{index_name}'.")

def update_index_mapping(index_name):
    cfg = _get_create_update_index_config()
    payload = _deep_merge(_default_update_mapping_payload(), cfg.get("update_mapping", {}))
    
    data = utils.make_request(f"{index_name}/_mapping", method='PUT', data=payload)
    if data and 'acknowledged' in data:
        print(f"Index '{index_name}' mapping updated successfully.")
        print(json.dumps(data, indent=4))
    else:
        print(f"Failed to update mapping for '{index_name}'.")

def update_index_settings(index_name):
    cfg = _get_create_update_index_config()
    payload = _deep_merge(_default_update_settings_payload(), cfg.get("update_settings", {}))
    
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
    default_index_name = utils.CONFIG.get("default_ingest_index", "logs-sample")
    parser.add_argument("--index", default=default_index_name, help=f"Index name (default: {default_index_name})")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_custom_index(args.index)
    elif args.action == "update_mapping":
        update_index_mapping(args.index)
    elif args.action == "update_settings":
        update_index_settings(args.index)
    elif args.action == "details":
        get_index_details(args.index)
