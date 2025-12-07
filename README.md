# Elasticsearch Daily Operations Scripts

This directory contains Python scripts to help with common daily operations for an Elasticsearch cluster. These scripts are designed to be lightweight and use only the standard Python library (no `pip install` required).

## Directory Structure

```
daily_ops_scripts/
├── monitor/
│   └── check_cluster_health.py
├── indices/
│   ├── manage_indices.py
│   └── create_update_index.py
├── ingest/
│   └── ingest_logs.py
├── search/
│   └── search_index.py
├── utils.py
├── ops.py  <-- Main Entrypoint
├── config.json <-- Configuration File
└── README.md
```

## Prerequisites

- Python 3.x installed.
- An Elasticsearch cluster running and accessible (default: `http://localhost:9200`).

## Configuration

Configuration is managed via `config.json`. You can modify this file to change the Elasticsearch host, log file paths, etc.

**Example `config.json`:**
```json
{
    "es_host": "http://localhost:9200",
    "log_file_path": "ingest/sample.log",
    "default_index_pattern": "*"
}
```

---

## Main Entrypoint: `ops.py`

The `ops.py` script serves as a single entrypoint for all operations.

### 1. Check Cluster Health

```bash
python3 ops.py health
```

### 2. Manage Indices

**List Indices**
```bash
python3 ops.py indices list
python3 ops.py indices list --pattern "log*"
```

**Create Index**
```bash
python3 ops.py indices create --name "my-index"
```

**Index Details**
```bash
python3 ops.py indices details --name "my-index"
```

**Delete Index**
```bash
python3 ops.py indices delete --name "my-index"
```

**Close/Open Index**
```bash
python3 ops.py indices close --name "my-index"
python3 ops.py indices open --name "my-index"
```

### 3. Ingest Logs

```bash
python3 ops.py ingest --index "logs-prod"
```

### 4. Search Index

```bash
# Search all documents (default size 10)
python3 ops.py search --index "logs-prod"

# Search with query string
python3 ops.py search --index "logs-prod" --query "status:error"

# Search with custom size
python3 ops.py search --index "logs-prod" --size 50
```

---

## Individual Scripts (Legacy Usage)

You can still run the individual scripts directly if needed.

- **Monitor**: `python3 monitor/check_cluster_health.py`
- **Indices**: `python3 indices/manage_indices.py list`
- **Ingest**: `python3 ingest/ingest_logs.py`
- **Search**: `python3 search/search_index.py --index "my-index"`

