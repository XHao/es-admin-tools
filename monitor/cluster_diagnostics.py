import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

def check_pending_tasks():
    print("\n--- Pending Cluster Tasks ---")
    data = utils.make_request("_cluster/pending_tasks")
    if data and 'tasks' in data:
        tasks = data['tasks']
        if not tasks:
            print("No pending tasks. (Good)")
        else:
            print(f"WARNING: {len(tasks)} pending tasks found!")
            for task in tasks[:5]: # Show top 5
                print(f"- {task['time_in_queue']}: {task['source']}")
            if len(tasks) > 5:
                print(f"... and {len(tasks) - 5} more.")
    else:
        print("Could not retrieve pending tasks.")

def check_thread_pool_rejections():
    print("\n--- Thread Pool Rejections (Write/Search) ---")
    # Get cat thread pool info for search and write
    data = utils.make_request("_cat/thread_pool/write,search?v&h=node_name,name,active,queue,rejected&format=json")
    
    has_rejections = False
    if data:
        print(f"{'Node':<20} {'Type':<10} {'Active':<8} {'Queue':<8} {'Rejected':<10}")
        print("-" * 60)
        for node in data:
            rejected = int(node.get('rejected', 0))
            if rejected > 0:
                has_rejections = True
            print(f"{node.get('node_name', 'N/A'):<20} {node.get('name', 'N/A'):<10} {node.get('active', 'N/A'):<8} {node.get('queue', 'N/A'):<8} {node.get('rejected', 'N/A'):<10}")
        
        if has_rejections:
            print("\nWARNING: Rejections detected! This indicates the cluster is overloaded.")
        else:
            print("\nNo rejections detected. (Good)")
    else:
        print("Could not retrieve thread pool stats.")

def check_circuit_breakers():
    print("\n--- Circuit Breakers ---")
    data = utils.make_request("_nodes/stats/breaker")
    
    tripped = False
    if data and 'nodes' in data:
        for node_id, node_stats in data['nodes'].items():
            breakers = node_stats.get('breakers', {})
            for breaker_name, stats in breakers.items():
                tripped_count = stats.get('tripped', 0)
                if tripped_count > 0:
                    tripped = True
                    print(f"WARNING: Node {node_stats.get('name')} - Breaker '{breaker_name}' tripped {tripped_count} times!")
        
        if not tripped:
            print("No circuit breakers tripped. (Good)")
    else:
        print("Could not retrieve circuit breaker stats.")

def check_translog_stats():
    print("\n--- Translog Stats (Persistence) ---")
    data = utils.make_request("_nodes/stats/indices/translog")
    
    if data and 'nodes' in data:
        print(f"{'Node':<20} {'Size':<15} {'Ops':<10} {'Uncommitted Ops':<15}")
        print("-" * 65)
        for node_id, node_stats in data['nodes'].items():
            name = node_stats.get('name', 'N/A')
            translog = node_stats.get('indices', {}).get('translog', {})
            size = translog.get('size_in_bytes', 0)
            ops = translog.get('operations', 0)
            uncommitted = translog.get('uncommitted_operations', 0)
            
            # Format size
            if size > 1024*1024*1024:
                size_str = f"{size/(1024*1024*1024):.2f} GB"
            elif size > 1024*1024:
                size_str = f"{size/(1024*1024):.2f} MB"
            else:
                size_str = f"{size/1024:.2f} KB"

            print(f"{name:<20} {size_str:<15} {ops:<10} {uncommitted:<15}")
            
            if uncommitted > 10000: # Arbitrary threshold for warning
                print(f"WARNING: High uncommitted operations on node {name}. Risk of long recovery.")
    else:
        print("Could not retrieve translog stats.")

def check_node_paths():
    print("\n--- Node Data Paths ---")
    data = utils.make_request("_nodes/settings")
    
    if data and 'nodes' in data:
        print(f"{'Node':<20} {'Data Path':<50}")
        print("-" * 70)
        for node_id, node_info in data['nodes'].items():
            name = node_info.get('name', 'N/A')
            settings = node_info.get('settings', {})
            path_settings = settings.get('path', {})
            data_path = path_settings.get('data', 'N/A')
            
            # Handle if data_path is a list (multiple data paths)
            if isinstance(data_path, list):
                data_path = ", ".join(data_path)
                
            print(f"{name:<20} {data_path:<50}")
    else:
        print("Could not retrieve node settings.")

def run_diagnostics():
    print("Running comprehensive cluster diagnostics...")
    check_pending_tasks()
    check_thread_pool_rejections()
    check_circuit_breakers()
    check_translog_stats()
    check_node_paths()

if __name__ == "__main__":
    run_diagnostics()
