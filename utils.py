import urllib.request
import urllib.error
import json
import sys
import os

# Load configuration
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
CONFIG = {}

def load_config():
    global CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                CONFIG = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}")
    else:
        # Default configuration
        CONFIG = {
            "es_host": "http://localhost:9200",
            "log_file_path": "./sample.log"
        }

load_config()
ES_HOST = CONFIG.get("es_host", "http://localhost:9200")

def make_request(endpoint, method='GET', data=None, headers=None):
    """
    Helper function to make HTTP requests to Elasticsearch.
    """
    if headers is None:
        headers = {}
    
    if data is not None and 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/json'

    if not endpoint.startswith("http"):
        url = f"{ES_HOST}/{endpoint.lstrip('/')}"
    else:
        url = endpoint

    if data is not None and isinstance(data, (dict, list)):
        data = json.dumps(data).encode('utf-8')
    elif data is not None and isinstance(data, str):
        data = data.encode('utf-8')

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read()
            if response_data:
                return json.loads(response_data)
            return {}
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {method} {url}: {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"Response body: {error_body}")
        except:
            pass
        return None
    except urllib.error.URLError as e:
        print(f"URL Error connecting to {url}: {e.reason}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
