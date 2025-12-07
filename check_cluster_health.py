import urllib.request
import json
import sys

ES_HOST = "http://localhost:9200"

def get_cluster_health():
    url = f"{ES_HOST}/_cluster/health"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.load(response)
            print("=== Cluster Health ===")
            print(f"Cluster Name: {data.get('cluster_name')}")
            print(f"Status: {data.get('status')}")
            print(f"Number of Nodes: {data.get('number_of_nodes')}")
            print(f"Number of Data Nodes: {data.get('number_of_data_nodes')}")
            print(f"Active Primary Shards: {data.get('active_primary_shards')}")
            print(f"Active Shards: {data.get('active_shards')}")
            print(f"Relocating Shards: {data.get('relocating_shards')}")
            print(f"Initializing Shards: {data.get('initializing_shards')}")
            print(f"Unassigned Shards: {data.get('unassigned_shards')}")
            return data
    except Exception as e:
        print(f"Error connecting to Elasticsearch at {ES_HOST}: {e}")
        return None

def get_nodes_info():
    url = f"{ES_HOST}/_cat/nodes?v&h=ip,heap.percent,ram.percent,cpu,load_1m,node.role,master,name&format=json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.load(response)
            print("\n=== Nodes Info ===")
            print(f"{'Name':<20} {'IP':<15} {'Role':<10} {'Master':<8} {'CPU%':<6} {'Heap%':<6} {'RAM%':<6} {'Load 1m':<8}")
            print("-" * 90)
            for node in data:
                print(f"{node.get('name', 'N/A'):<20} {node.get('ip', 'N/A'):<15} {node.get('node.role', 'N/A'):<10} {node.get('master', 'N/A'):<8} {node.get('cpu', 'N/A'):<6} {node.get('heap.percent', 'N/A'):<6} {node.get('ram.percent', 'N/A'):<6} {node.get('load_1m', 'N/A'):<8}")
    except Exception as e:
        print(f"Error fetching nodes info: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["help", "-h", "--help"]:
        print("Usage: python3 check_cluster_health.py")
        print("Checks the health of the Elasticsearch cluster and lists node information.")
        sys.exit(0)

    health = get_cluster_health()
    if health:
        get_nodes_info()
