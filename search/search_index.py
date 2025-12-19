import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import argparse
import json
from urllib.parse import quote

def _coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


DEFAULT_SIZE = _coerce_int(utils.CONFIG.get("default_search_size", 10), 10)

def search_index(index_name, query=None, size=DEFAULT_SIZE):
    endpoint = f"{index_name}/_search"
    params = [f"size={size}"]
    
    if query:
        # Simple URI search
        params.append(f"q={quote(query)}")
    
    # Join params
    query_string = "&".join(params)
    full_endpoint = f"{endpoint}?{query_string}"
    
    data = utils.make_request(full_endpoint)
    
    if data:
        print(f"=== Search Results ({index_name}) ===")
        hits_info = data.get('hits', {})
        total = hits_info.get('total', {}).get('value', 0) if isinstance(hits_info.get('total'), dict) else hits_info.get('total', 0)
        print(f"Total Hits: {total}")
        
        hits = hits_info.get('hits', [])
        if not hits:
            print("No hits to display.")
        else:
            print("-" * 40)
            for hit in hits:
                source = hit.get('_source', {})
                print(json.dumps(source, indent=2))
                print("-" * 40)
    else:
        print("No results found or error occurred.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Elasticsearch Index")
    parser.add_argument("--index", required=True, help="Index to search")
    parser.add_argument("--query", help="Query string (Lucene syntax, e.g. 'field:value')")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help=f"Number of results (default: {DEFAULT_SIZE})")
    
    args = parser.parse_args()
    
    search_index(args.index, args.query, args.size)
