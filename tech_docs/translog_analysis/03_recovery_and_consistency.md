# Translog Recovery and Consistency

The Translog is the ultimate source of truth for recovering data that was acknowledged to the client but not yet part of a safe Lucene commit.

## 1. Local Recovery (Node Startup)

When a shard starts up (e.g., after a node restart or crash), it must ensure its state is consistent.

### The Recovery Process
1.  **Initialization**:
    - The `Translog` component initializes by calling `recoverFromFiles()`.
    - It reads the `translog.ckp` file to identify the current generation and the safe offset.
    - It opens the `TranslogWriter` for the current generation and `TranslogReader`s for any previous generations that haven't been trimmed.

2.  **Replay**:
    - The `InternalEngine` uses `restoreLocalHistoryFromTranslog()` to replay operations.
    - **Starting Point**: It identifies the **Local Checkpoint**—the sequence number up to which all operations have been successfully processed and committed.
    - **Operation Replay**: It iterates through the Translog operations starting from the Local Checkpoint.
    - Each operation is re-indexed into Lucene. This restores the in-memory buffer and file system cache segments that were lost during the crash.

3.  **Consistency Check**:
    - Once replay is complete, the shard is marked as active, and the Translog is ready to accept new writes.

## 2. Peer Recovery (Replica Synchronization)

When a replica shard is initialized or comes back online after being disconnected, it needs to synchronize with the primary shard.

### Phase 1: File Copy
- The primary creates a snapshot of the Lucene index and sends the segment files to the replica.

### Phase 2: Translog Replay (Operations)
- While Phase 1 is happening, the primary continues to accept new write operations.
- Once the file copy is done, the replica is likely slightly behind the primary.
- Instead of copying the entire index again, the primary sends the "gap" operations from its Translog.
- **Snapshotting**: The `Translog.newSnapshot()` method creates a stream of operations within a specific sequence number range (from the replica's last known state to the current state).
- These operations are sent over the network and replayed on the replica to bring it fully in sync.

## 3. Data Consistency Guarantees

- **Sequence Numbers**: Every operation is assigned a unique sequence number (`seq_no`) and primary term. The Translog stores these to ensure operations are applied in the correct order during recovery.
- **Checksums**: Every entry in the Translog is checksummed. During reading/recovery, checksums are verified to detect bit rot or file corruption.
- **UUID Linking**: The Lucene commit point stores the Translog UUID. This prevents a shard from accidentally recovering from a Translog that belongs to a different history or a different shard allocation.
