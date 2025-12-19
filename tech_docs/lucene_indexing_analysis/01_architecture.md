# Lucene Indexing Architecture

## Overview

Apache Lucene is a library for building a full‑text search index. Its indexing pipeline is designed around two ideas:

1. **Write new data as immutable segment files** (append-only files; segments are never modified in-place).
2. **Publish new search views by swapping a commit point or reopening a reader**, rather than rewriting the whole index.

This architecture enables high indexing throughput, near real-time (NRT) search, and crash safety via durable commit points.

## Core Building Blocks

### 1) Document and Field model
- A **Document** is a bag of **Fields**.
- A Field can contribute multiple “views” of the same logical value, such as:
  - **Inverted index** (for full-text search)
  - **Stored fields** (for retrieval)
  - **Doc values** (for sorting/aggregations)
  - **Points** (BKD trees for numeric/date/geo range queries)
  - **Vectors** (for approximate nearest neighbor / semantic search, if configured)

Lucene indexes are effectively multiple columnar/row stores built side-by-side, depending on what you enable per field.

### 2) Analysis pipeline (text → tokens)
For text fields, indexing starts with an **Analyzer**, which typically consists of:
- **Character filters** (optional): normalize the raw string (e.g., strip HTML)
- **Tokenizer**: split text into tokens
- **Token filters**: transform tokens (lowercasing, stemming, stopword removal, synonyms, etc.)

The output is a stream of tokens that carry:
- term text
- position (for phrase queries)
- offsets (for highlighting)
- optional payloads

### 3) IndexWriter: the ingestion engine
`IndexWriter` is Lucene’s main indexing component. It:
- accepts documents/updates/deletes
- buffers changes in memory
- flushes buffered changes into new on-disk segments
- manages merges (compaction)
- controls durability via commit points

Key idea: most indexing is performed against in-memory structures first; disk IO happens in large sequential writes when a flush occurs.

### 4) In-memory indexing structures
When documents are added, Lucene builds in-memory structures such as:
- a per-field term dictionary and postings buffers
- stored fields buffers
- doc values buffers
- delete/update tracking

These structures are optimized to be written out as a segment in one shot.

### 5) Segments: immutable index partitions
A Lucene index is a set of **segments**. Each segment is a standalone mini-index with:
- postings + term dictionary
- stored fields
- doc values
- points/vectors (if any)
- a live docs bitset (or equivalent) to represent deletions

Segments are immutable once written. Updates and deletions are applied by:
- writing new segments and/or
- marking old docs as deleted (and possibly writing doc-values updates)

### 6) Directory and files
Lucene reads/writes to a `Directory` abstraction (e.g., `FSDirectory` for filesystem). On disk you’ll see:
- many per-segment files (format depends on codec)
- a **commit point** file named `segments_N`

`segments_N` is the authoritative manifest describing which segment files form the current committed index state.

### 7) Codec: how bytes are laid out
The **Codec** defines the on-disk format (postings, stored fields, doc values, points, etc.). Lucene’s default codec is tuned for general use, but codecs can be customized for specialized needs.

## Search Views: Commit vs NRT

Lucene has two ways to make indexed data visible:

### A) Commit (durable, slower)
A **commit** writes a new `segments_N` file (a new commit point) and fsyncs index files according to the directory implementation.
- Guarantees durability for the committed state.
- Makes the committed segments visible to readers that open from the directory.

### B) Near Real-Time (fast visibility)
Lucene can also expose new segments without a full commit by reopening a reader from the `IndexWriter` (often via `DirectoryReader.open(IndexWriter)`).
- Makes recently flushed segments searchable quickly.
- Does **not** necessarily guarantee the same durability semantics as a full commit.

This split (fast visibility vs durable commit) is central to how systems like Elasticsearch provide near real-time search while controlling fsync frequency.

## Merges: keeping segment counts manageable
As indexing continues, many small segments are created. Searching too many segments increases overhead, so Lucene merges segments in the background.

Merges:
- read multiple existing segments
- rewrite them into a larger segment
- apply deletions (and consolidate doc-values updates)
- delete old segment files once safe

This is conceptually similar to LSM compaction: high write throughput with periodic background consolidation.

## Mental Model (high level)

```text
Documents
  │
  ▼
Analysis (text) + field encoding (doc values, points, stored)
  │
  ▼
IndexWriter buffers (RAM)
  │   (flush triggered by RAM limits / doc count / explicit)
  ▼
New immutable segment files
  │
  ├─ NRT: reopen reader -> searchable soon
  │
  └─ Commit: write segments_N + fsync -> durable state
        │
        ▼
Background merges -> fewer, larger segments
```
