# Elasticsearch Translog Architecture

## Overview

The **Translog (Transaction Log)** is a fundamental component of Elasticsearch's storage engine, designed to ensure data durability and consistency. It acts as a write-ahead log (WAL) for the Lucene index. Since committing data to Lucene (an `fsync` operation) is expensive, Elasticsearch writes operations to the Translog first—which is sequential and fast—and only performs a Lucene commit periodically.

## Key Responsibilities

1.  **Durability**: Ensures that operations acknowledged to the client are persisted to disk, even if the node crashes before a Lucene commit.
2.  **Atomicity**: Provides a mechanism to replay operations that were not yet part of the last safe Lucene commit upon node startup.
3.  **Real-time Search (Indirectly)**: While the Translog itself isn't searched, it allows the system to acknowledge writes quickly while relying on the in-memory Lucene buffer for near real-time search (via Refresh).

## Core Components

### 1. `Translog.java`
The main entry point and facade for managing the transaction log. It coordinates the current write operations and manages the lifecycle of read-only files from previous generations.
- **Location**: `server/src/main/java/org/elasticsearch/index/translog/Translog.java`
- **Role**: Manages the `TranslogWriter` (current generation) and a list of `TranslogReader`s (older generations).

### 2. `TranslogWriter.java`
Handles writing operations to the active Translog file.
- **Location**: `server/src/main/java/org/elasticsearch/index/translog/TranslogWriter.java`
- **Role**: 
    - Serializes operations (Index, Delete, NoOp) into a byte stream.
    - Buffers writes in memory (`RecyclerBytesStreamOutput`) before flushing to disk.
    - Manages `fsync` behavior based on the `index.translog.durability` setting (`request` vs. `async`).

### 3. `TranslogReader.java`
Provides read access to immutable Translog files from previous generations.
- **Location**: `server/src/main/java/org/elasticsearch/index/translog/TranslogReader.java`
- **Role**: Used primarily during recovery to replay operations or during peer recovery to send operations to replicas.

### 4. `Checkpoint`
A metadata structure ensuring atomic views of the Translog.
- **File**: `translog.ckp`
- **Content**: Contains the current generation ID, the offset (size) of the file, and sequence number stats (min/max seq_no).
- **Role**: Allows the reader to know exactly how much of the file is safe to read, preventing partial reads of incomplete writes.

## File Structure on Disk

Inside an index shard's directory, the `translog` folder contains:

*   **`translog-N.tlog`**: The actual log files containing serialized operations. `N` is the generation ID.
*   **`translog.ckp`**: The checkpoint file pointing to the current active generation.
*   **`translog-N.ckp`**: Checkpoint files for older, immutable generations.

```text
shard_dir/
└── translog/
    ├── translog-42.tlog  (Older generation, read-only)
    ├── translog-43.tlog  (Current generation, active write)
    └── translog.ckp      (Points to generation 43)
```
