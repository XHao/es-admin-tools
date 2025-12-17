# Translog Performance Optimization

Optimizing the Translog involves balancing **data safety** (durability) against **indexing throughput** and **latency**. Since the Translog is a write-ahead log that sits in the critical path of indexing operations, its configuration directly impacts write performance.

## 1. Durability Settings (The Big Knob)

The most significant performance lever is the `index.translog.durability` setting.

### `request` (Default) - Maximum Safety
*   **Behavior**: `fsync` is called after *every* indexing request (bulk, index, delete).
*   **Performance Impact**: High disk I/O overhead. Latency is bound by the disk's ability to sync.
*   **Use Case**: Financial data, critical systems where zero data loss is acceptable.

### `async` - Maximum Performance
*   **Behavior**: `fsync` happens in the background every `index.translog.sync_interval` (default 5s).
*   **Performance Impact**: Significantly higher throughput and lower latency. The disk I/O is batched.
*   **Risk**: If a node crashes, you lose operations acknowledged in the last `sync_interval`.
*   **Configuration**:
    ```json
    PUT /my-index/_settings
    {
      "index.translog.durability": "async",
      "index.translog.sync_interval": "5s"
    }
    ```

## 2. Flush Thresholds (controlling Lucene Commits)

Flushing moves data from the Translog to Lucene segments. Frequent flushes are expensive.

### `index.translog.flush_threshold_size`
*   **Default**: `512mb`
*   **Optimization**: Increasing this value allows the Translog to grow larger before triggering a flush.
*   **Benefit**: Reduces the frequency of expensive Lucene commits (merging segments, writing to disk). Good for heavy indexing workloads.
*   **Trade-off**: A larger Translog means **longer recovery time** if a node restarts, as more operations need to be replayed.

## 3. Generation Thresholds (File Management)

### `index.translog.generation_threshold_size`
*   **Default**: `64mb`
*   **Optimization**: Controls when to roll over to a new Translog file.
*   **Benefit**: Keeping this reasonable prevents individual files from becoming unwieldy. Increasing it slightly might reduce file handle churn, but the default is usually sufficient.

## 4. Hardware & OS Level Optimizations

Since Translog relies heavily on sequential writes and `fsync`:

*   **SSD/NVMe**: Essential for high-performance indexing. The latency of `fsync` on spinning disks is a major bottleneck for `durability: request`.
*   **Separate Disk (Advanced)**: In extreme cases, mounting the Translog directory on a separate physical device from the Lucene index files can reduce I/O contention, though Elasticsearch doesn't natively support splitting them easily within a single data path configuration (they usually reside in the same shard directory).
*   **OS Page Cache**: Ensure the OS has enough RAM to buffer writes before they are synced.

## 5. Bulk Indexing Strategy

*   **Larger Batches**: When using `durability: request`, sending larger bulk requests is more efficient than many small requests. One bulk request = one `fsync`, regardless of how many documents are in it.
    *   *Example*: 1000 docs in 1 request = 1 fsync. 1000 docs in 1000 requests = 1000 fsyncs.

## Summary Checklist

| Goal | Action | Trade-off |
| :--- | :--- | :--- |
| **Max Throughput** | Set `durability: async` | Potential data loss on crash (last 5s) |
| **Reduce I/O Wait** | Use SSDs | Cost |
| **Reduce Flush Overhead** | Increase `flush_threshold_size` (e.g., 1GB) | Slower node recovery |
| **Optimize Network/Disk** | Use Bulk API with optimal batch size | Client-side complexity |
