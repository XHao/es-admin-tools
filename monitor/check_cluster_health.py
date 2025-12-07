import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import argparse

def get_cluster_health():
    data = utils.make_request("_cluster/health")
    if data:
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
    return None

def get_nodes_info():
    data = utils.make_request("_cat/nodes?v&h=ip,heap.percent,ram.percent,cpu,load_1m,node.role,master,name&format=json")
    if data:
        print("\n=== Nodes Info ===")
        print(f"{'Name':<20} {'IP':<15} {'Role':<10} {'Master':<8} {'CPU%':<6} {'Heap%':<6} {'RAM%':<6} {'Load 1m':<8}")
        print("-" * 90)
        for node in data:
            print(f"{node.get('name', 'N/A'):<20} {node.get('ip', 'N/A'):<15} {node.get('node.role', 'N/A'):<10} {node.get('master', 'N/A'):<8} {node.get('cpu', 'N/A'):<6} {node.get('heap.percent', 'N/A'):<6} {node.get('ram.percent', 'N/A'):<6} {node.get('load_1m', 'N/A'):<8}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Checks the health of the Elasticsearch cluster and lists node information.")
    args = parser.parse_args()

    health = get_cluster_health()
    if health:
        get_nodes_info()
