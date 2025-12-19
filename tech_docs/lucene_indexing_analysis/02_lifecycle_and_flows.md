# Lucene Indexing Lifecycle and Flows

This chapter walks through the indexing process as a sequence of events, highlighting what happens in memory, what is written to disk, and when changes become visible to search.

## 1) Add a document: from API call to in-memory buffers

Indexing begins when your application calls something like:
- `IndexWriter.addDocument(doc)`
- `IndexWriter.updateDocument(term, doc)`

At a high level, Lucene does the following:

1. **Per-field processing**
   - For text fields: run the Analyzer to produce tokens.
   - For numeric/date/geo fields: encode values for points (BKD).
   - For doc values fields: encode columnar values.
   - For stored fields: serialize values for later retrieval.

2. **Build inverted index data** (text / term-based fields)
   - Create term → postings mappings.
   - Record docIDs, term frequencies, positions, offsets (if enabled).

3. **Record deletes/updates intent**
   - A delete/update generally means “this doc should no longer match future readers”.
   - Lucene usually represents this by writing new docs and later applying a deletion marker to old docs.

Result: most work lands in **RAM buffers** inside the IndexWriter, not on disk immediately.

## 2) Flush: RAM buffers become a new segment

A **flush** is when Lucene writes buffered in-memory index data as a new on-disk segment.

Flush triggers:
- RAM usage exceeds configured thresholds (e.g., RAM buffer size)
- too many buffered documents
- explicit calls (rare)
- internal safety reasons

What flush produces:
- a new segment with postings/stored/docvalues/points/vectors as applicable
- segment metadata

Important: flush is primarily about converting RAM → on-disk segment files. It is not the same thing as a durable “commit”.

## 3) Visibility: NRT reopen vs directory-open readers

After a flush, the data exists as segment files, but whether search can see it depends on how readers are opened.

### A) Near Real-Time (NRT) reopen (common in servers)
- A reader opened from the `IndexWriter` can see newly flushed segments quickly.
- Operationally: reopen a `DirectoryReader` (or `IndexSearcher`) periodically.

Typical loop:

```text
index documents (RAM)
   │
flush to segment files
   │
refresh (reopen reader)  -> search sees new docs
```

This is the backbone of near real-time search.

### B) Open from the directory (commit-based)
- A reader opened from the index directory (filesystem) sees only committed segments.
- Requires a commit point (`segments_N`) that includes those segments.

## 4) Updates and deletes: what “update” means in Lucene

Lucene does not update documents in place. An “update” is typically:

1. Add a new document version.
2. Mark prior matching documents as deleted.

Deletes are tracked and applied in a way that is safe and performant:
- a “live docs” structure indicates which docIDs are still visible
- deletions become effective for new searchers after reopen

Doc values updates exist, but are specialized and come with tradeoffs (they may create additional per-segment update files and can increase merge costs).

## 5) Commit: publish a durable commit point

A **commit** publishes a new durable index state by writing a new `segments_N` file and ensuring the relevant files are on stable storage.

Conceptually:

```text
segment files already exist
   │
write new segments_N (commit point)
   │
fsync metadata + files (Directory-dependent)
   ▼
durable committed index
```

A commit does not necessarily make indexing faster or more visible; it primarily establishes crash-consistent durability for the index state.

## 6) Background merges: compaction over time

As flushes happen repeatedly, you get many segments. Lucene’s merge policy decides when to merge.

Merge flow:

```text
many small segments
   │
select merge candidates (MergePolicy)
   │
rewrite into bigger segment
   │
apply deletions & consolidate updates
   │
swap in new segment, remove old ones
```

Why merges matter:
- fewer segments improves query performance (less per-segment overhead)
- merges reclaim space from deleted documents
- merges increase write amplification and IO, so tuning can matter

## 7) Putting it together: end-to-end timeline

Here’s a simplified timeline for a continuous ingestion workload:

1. Add documents → analyzed and buffered in RAM.
2. Flush occurs → new segment files are written.
3. Refresh/NRT reopen occurs → new segment becomes searchable.
4. Periodic commit occurs → durable `segments_N` is published.
5. Background merges run → reduce segment count and reclaim deletes.

If you’re coming from Elasticsearch:
- “refresh” maps closely to Lucene NRT reopen semantics.
- “flush” and “commit” have related but not identical meanings across layers; in Lucene, commit is the durable publication of the index state.
