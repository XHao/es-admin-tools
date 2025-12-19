import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import json
import argparse


def _coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

INDEX_NAME = utils.CONFIG.get("default_ingest_index", "logs-sample")
# Use configured path or fallback to default relative path
LOG_FILE_PATH = utils.CONFIG.get("log_file_path", "./sample.log")
BATCH_SIZE = _coerce_int(utils.CONFIG.get("ingest_batch_size", 500), 500)

def ingest_logs(index_name=INDEX_NAME):
    # Resolve absolute path
    # If LOG_FILE_PATH is absolute, os.path.join will use it directly.
    # If relative, it will be relative to this script's directory (ingest/).
    # However, the config path might be relative to the root of daily_ops_scripts or absolute.
    # Let's assume relative paths in config are relative to daily_ops_scripts root for consistency,
    # OR we just handle it carefully.
    
    # If the path starts with ../ or ./, treat it relative to THIS script for backward compatibility 
    # if it was hardcoded that way, but now it comes from config.
    # Let's try to resolve it relative to the config file location (daily_ops_scripts root) if possible,
    # or just use it as is if absolute.
    
    if os.path.isabs(LOG_FILE_PATH):
        file_path = LOG_FILE_PATH
    else:
        # Assume relative to daily_ops_scripts root (where config.json is)
        # utils.py is in daily_ops_scripts/
        base_dir = os.path.dirname(os.path.abspath(utils.__file__))
        file_path = os.path.join(base_dir, LOG_FILE_PATH)

    if not os.path.exists(file_path):
        # Fallback: try relative to this script (ingest/) just in case
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fallback_path = os.path.join(script_dir, LOG_FILE_PATH)
        if os.path.exists(fallback_path):
            file_path = fallback_path
        else:
            print(f"Error: Log file not found at {file_path} or {fallback_path}")
            return

    print(f"Reading logs from {file_path}...")
    
    bulk_data = []
    count = 0
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Create action line
                action = {"index": {"_index": index_name}}
                bulk_data.append(json.dumps(action))
                bulk_data.append(line)
                count += 1
                
                # Send in batches of 500
                if count % BATCH_SIZE == 0:
                    send_bulk_request(bulk_data)
                    bulk_data = []
                    print(f"Processed {count} documents...")

        # Send remaining
        if bulk_data:
            send_bulk_request(bulk_data)
            print(f"Processed {count} documents (Finished).")
            
    except Exception as e:
        print(f"Error reading file: {e}")

def send_bulk_request(bulk_data):
    # Bulk data must end with a newline
    data_str = "\n".join(bulk_data) + "\n"
    
    # Use utils.make_request
    # We explicitly set Content-Type to application/x-ndjson, though application/json often works too.
    result = utils.make_request("_bulk", method="POST", data=data_str, headers={'Content-Type': 'application/x-ndjson'})
    
    if result and result.get('errors'):
        print("Warning: Some documents failed to index.")
        # In a real script, you'd inspect result['items'] for errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest sample logs into Elasticsearch")
    parser.add_argument("--index", default=INDEX_NAME, help=f"Target index name (default: {INDEX_NAME})")
    args = parser.parse_args()

    # Update global INDEX_NAME if provided
    if args.index:
        INDEX_NAME = args.index

    print(f"Ingesting logs into index '{INDEX_NAME}'...")
    ingest_logs()
