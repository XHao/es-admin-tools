import urllib.request
import json
import os
import sys

ES_HOST = "http://localhost:9200"
INDEX_NAME = "logs-sample"
LOG_FILE_PATH = "../tools/log-ingester/sample.log" # Relative path from daily_ops_scripts/

def ingest_logs():
    # Resolve absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, LOG_FILE_PATH)

    if not os.path.exists(file_path):
        print(f"Error: Log file not found at {file_path}")
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
                action = {"index": {"_index": INDEX_NAME}}
                bulk_data.append(json.dumps(action))
                bulk_data.append(line)
                count += 1
                
                # Send in batches of 500
                if count % 500 == 0:
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
    url = f"{ES_HOST}/_bulk"
    # Bulk data must end with a newline
    data_str = "\n".join(bulk_data) + "\n"
    data_bytes = data_str.encode('utf-8')
    
    req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.load(response)
            if result.get('errors'):
                print("Warning: Some documents failed to index.")
                # In a real script, you'd inspect result['items'] for errors
            else:
                pass # Success
    except Exception as e:
        print(f"Error sending bulk request: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["help", "-h", "--help"]:
        print("Usage: python3 ingest_logs.py")
        print(f"Ingests logs from {LOG_FILE_PATH} into index '{INDEX_NAME}'.")
        sys.exit(0)

    print(f"Ingesting logs into index '{INDEX_NAME}'...")
    ingest_logs()
