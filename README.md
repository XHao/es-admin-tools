# Elasticsearch Daily Operations Scripts

This directory contains Python scripts to help with common daily operations for an Elasticsearch cluster. These scripts are designed to be lightweight and use only the standard Python library (no `pip install` required).

## Prerequisites

- Python 3.x installed.
- An Elasticsearch cluster running and accessible (default: `http://localhost:9200`).

## Configuration

All scripts have a global variable `ES_HOST` at the top of the file.
```python
ES_HOST = "http://localhost:9200"
```
If your cluster is running on a different host or port, please update this variable in the respective script.

---

## 1. Check Cluster Health (`check_cluster_health.py`)

This script provides a quick overview of the cluster's health and the status of its nodes.

### Usage
```bash
python3 check_cluster_health.py
```

### Output
- **Cluster Health**: Status (Green/Yellow/Red), node counts, and shard information.
- **Nodes Info**: A table listing nodes, their roles, IP addresses, CPU usage, Heap usage, and Load.

---

## 2. Manage Indices (`manage_indices.py`)

This script allows you to list, delete, close, and open indices.

### Usage

**List Indices**
List all indices or filter by a pattern.
```bash
# List all indices
python3 manage_indices.py list

# List indices matching a pattern (e.g., "log*")
python3 manage_indices.py list --index "log*"
```

**Delete an Index**
Permanently remove an index.
```bash
python3 manage_indices.py delete --index my-index-name
```
*Note: You will be prompted to confirm the deletion.*

**Close an Index**
Close an index to save memory (it becomes read/write blocked but remains on disk).
```bash
python3 manage_indices.py close --index my-index-name
```

**Open an Index**
Re-open a closed index.
```bash
python3 manage_indices.py open --index my-index-name
```

---

## 3. Ingest Logs (`ingest_logs.py`)

This script demonstrates how to ingest data into the cluster. It reads a sample log file (`../tools/log-ingester/sample.log`) and indexes the documents into an index named `logs-sample`.

### Usage
```bash
python3 ingest_logs.py
```

### Details
- **Source File**: `../tools/log-ingester/sample.log`
- **Target Index**: `logs-sample`
- **Method**: Uses the Elasticsearch `_bulk` API for efficient ingestion.

---

## 4. Create and Update Index (`create_update_index.py`)

This script demonstrates how to create an index with custom settings and mappings, and how to update them later.

### Usage

**Create Index**
Creates an index named `my-custom-index` (default) with a custom analyzer and initial mapping.
```bash
python3 create_update_index.py create
```

**Update Mapping**
Adds new fields (`category`, `tags`) to the existing index mapping.
```bash
python3 create_update_index.py update_mapping
```

**Update Settings**
Updates dynamic settings (e.g., `refresh_interval`) for the index.
```bash
python3 create_update_index.py update_settings
```

**Custom Index Name**
You can specify a custom index name for any action:
```bash
python3 create_update_index.py create --index my-blog-index
```
