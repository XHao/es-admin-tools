# Translog Lifecycle and Data Flows

This document details how the Translog interacts with the `InternalEngine` during the primary phases of data processing: Indexing, Refreshing, and Flushing.

## 1. Indexing Flow (Write Path)

When a document is indexed, updated, or deleted, the operation follows a strict path to ensure durability before acknowledgement.

### Step-by-Step Process
1.  **Lucene Indexing**: 
    The `InternalEngine` first applies the operation to the in-memory Lucene `IndexWriter` via `indexIntoLucene`. This updates the inverted index in memory but is not yet safe on disk.
    
2.  **Translog Append**:
    If the Lucene operation is successful, the operation is added to the Translog via `translog.add(Operation)`.
    - The `TranslogWriter` serializes the operation, including metadata like `_id`, `_source`, `seq_no`, `primary_term`, and `version`.
    - The data is written to an in-memory buffer.

3.  **Sync (Durability Enforcement)**:
    - **Request Durability (Default)**: If `index.translog.durability` is set to `request`, the `TranslogWriter` forces an `fsync` of the file to disk before the `index()` method returns. This guarantees the data is safe even if the node crashes immediately after.
    - **Async Durability**: If set to `async`, the writer syncs in the background at the configured `index.translog.sync_interval` (default 5s). This offers higher performance at the risk of losing recent operations during a crash.

4.  **Checkpoint Update**:
    The in-memory `Checkpoint` is updated to reflect the new write offset and sequence numbers.

## 2. Refresh Flow (Search Visibility)

A **Refresh** operation makes the operations performed since the last refresh visible for search.

- **Mechanism**: It triggers a Lucene reopen, creating new segments from the in-memory buffer.
- **Translog Interaction**: 
    - **Crucially, Refresh does NOT clear the Translog.**
    - The new Lucene segments exist only in the file system cache (OS page cache) and have not been `fsync`ed.
    - If the node crashes, these segments would be lost. Therefore, the Translog must be preserved to replay these operations during recovery.

## 3. Flush Flow (Persistence & Cleanup)

A **Flush** is the process of committing data to the Lucene index on disk and clearing the Translog. It is triggered when the Translog reaches a certain size (`index.translog.flush_threshold_size`) or after a period of time.

### Step-by-Step Process
1.  **Roll Generation**: 
    The `InternalEngine` calls `translog.rollGeneration()`.
    - The current `TranslogWriter` is closed and converted into an immutable `TranslogReader`.
    - A new `TranslogWriter` is created with an incremented generation ID (e.g., `translog-4.tlog` -> `translog-5.tlog`).

2.  **Lucene Commit**: 
    The `InternalEngine` calls `commitIndexWriter()`.
    - This performs a Lucene commit, which `fsync`s all segments to disk.
    - **Metadata Link**: The commit data includes the **Translog Generation** (UUID and generation ID) to link the persistent Lucene index state with the corresponding Translog generation.

3.  **Trim Translog**: 
    Once the Lucene commit is successful, the older Translog files (from the previous generation) are no longer needed for recovery because the data is safely persisted in Lucene.
    - `translog.trimUnreferencedReaders()` is called.
    - The `TranslogDeletionPolicy` determines which files are safe to delete.

## Summary of States

| Phase | Lucene State | Translog State | Durability |
| :--- | :--- | :--- | :--- |
| **Indexing** | In-memory buffer | Appended & Fsynced (Request) | High |
| **Refresh** | New Segments (Cached) | Unchanged (Accumulating) | High |
| **Flush** | Segments Fsynced | Rolled & Trimmed | High |
