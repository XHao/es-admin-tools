# Lucene Recovery and Consistency

This chapter explains how Lucene maintains a crash-consistent index on disk, what guarantees you do and don’t get without a commit, and how deletions/merges interact with consistency.

## The Key Concept: Commit Points

A Lucene index’s durable state is defined by a **commit point**, represented by a `segments_N` file.

- `segments_N` lists all segment files that comprise the committed index.
- A new commit point is created on each successful commit.
- If a crash happens, Lucene recovers by reading the latest intact commit point.

Because segments are immutable, the commit point acts like an atomic “manifest switch” to a new version of the index.

## Two-Phase Commit (high level)

A safe commit generally follows a “write everything, then publish” approach:

1. Ensure new segment files (and any related metadata) are written.
2. Write a new `segments_N` file that references those new segments.
3. Ensure the commit point is durably persisted (fsync semantics depend on the Directory/FS).

If a crash happens mid-way:
- Old commit point remains valid.
- New, partially written state is ignored because it is not referenced by a durable `segments_N`.

## What Happens Without a Commit?

Near real-time search can see changes after flush + reopen, but:
- those changes may not be part of the last durable commit point
- after a crash, Lucene will roll back to the last committed `segments_N`

In other words:
- **NRT visibility** is about what a searcher can see now.
- **Commit durability** is about what survives process/OS/power failure.

Many systems add an external write-ahead log (WAL) to bridge this gap.

## Checksum and Corruption Detection

Lucene writes checksums for many files and performs integrity checks.
On startup or during reads, Lucene can detect:
- truncated files
- checksum mismatches

Corruption handling is ultimately application-defined (e.g., fail the shard, restore from replica, rebuild index).

## Deletes and Updates: Consistency Semantics

### Deletions
Deletes are recorded as metadata (conceptually “these docIDs are not live”).
- A segment may have a “live docs” bitset.
- New searchers reflect deletions after reopen.
- Merges physically drop deleted documents, reclaiming space.

### Updates
Most updates are implemented as:
- add new doc
- delete old doc(s)

This yields consistent query semantics as long as your application uses stable identifiers and update terms correctly.

### Doc values updates
Doc values updates are possible but are not “in-place” in the classic sense; they typically create additional update structures that are later folded in during merges. This affects:
- IO patterns
- merge cost
- latency for heavy update workloads

## Merges and Crash Safety

Merges rewrite existing segments into a new segment.
Crash safety comes from the same “publish by manifest” rule:
- merge outputs are written as new files
- only after completion does the index metadata reference the new merged segment
- old segments are deleted only when the new state is safely published and no readers need the old files

This gives merges transactional behavior from the perspective of committed states.

## Reader Consistency (Snapshot Semantics)

Once a searcher is created, it sees a stable snapshot of the index at that point in time.
- it won’t see newly indexed docs until it is reopened
- it remains correct even while indexing and merges proceed in the background

Lucene achieves this via immutable segments and reference counting of files behind the scenes.

## Relating This to Elasticsearch (brief)

Lucene alone can only guarantee durability at commit points. Elasticsearch (and similar systems) typically rely on:
- Lucene commits for durable index metadata
- a separate WAL (translog) to replay acknowledged operations that were visible/NRT but not committed

This is why translog exists: it closes the gap between “fast NRT indexing” and “expensive durable commit”.
