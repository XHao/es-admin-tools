# Lucene Indexing Performance Optimization

This chapter focuses on practical performance levers for Lucene indexing. The goal is to keep throughput high and latency predictable while avoiding pathological merge/segment behavior.

## 1) Measure the right things

Indexing performance issues typically show up as one (or more) of:
- CPU-bound analysis (tokenization, stemming, synonyms)
- IO-bound flush or merge activity
- merge backlog (segment counts grow, disk usage grows)
- GC/memory pressure from large buffers or large transient objects

Useful indicators:
- segment count and segment size distribution
- merge time and merge queue depth
- IO utilization and write amplification symptoms
- indexing thread utilization and analysis CPU

## 2) Reduce analysis cost (often the #1 CPU driver)

Tactics:
- simplify analyzer chains where possible
- avoid overly expansive synonym strategies (especially at index time) if they multiply token counts
- ensure char filters/token filters aren’t doing expensive regex work unnecessarily

Heuristic:
- if indexing throughput improves dramatically when indexing only “keyword” fields, analysis is likely your bottleneck.

## 3) Control segment churn (flush behavior)

Too many tiny segments cause:
- higher search overhead
- aggressive merging
- higher write amplification

Levers:
- increase RAM buffer size (within memory budget)
- batch documents rather than indexing one-at-a-time with costly refresh patterns
- avoid forcing frequent flush/commit cycles

Tradeoff:
- larger buffers increase peak memory usage and may increase the amount of work lost if your application doesn’t have a WAL and you crash before commit.

## 4) Manage merges (the compaction tax)

Merges are necessary but expensive. If they’re constantly saturated:
- your disk may not keep up with your ingestion rate
- you may need to tune merge policy/scheduler or scale storage

Practical approaches:
- increase merge concurrency only if storage can handle it
- avoid configurations that create many small segments
- watch for heavy update/delete workloads, which increase merge cost because deletions must be applied and reclaimed

Rule of thumb:
- stable systems have merges that “keep up” over time (no persistent merge backlog).

## 5) Be intentional about field features

Every enabled feature adds indexing work and index size.

Common tradeoffs:
- **stored fields**: great for retrieval, but increase IO and storage
- **doc values**: required for sorting/aggregations, but can dominate index size for wide schemas
- **positions/offsets**: required for phrase queries/highlighting, but increase postings size
- **norms**: useful for scoring, but can be disabled for non-scored fields
- **vectors**: powerful, but can be CPU/memory intensive; tune dimensions and similarity carefully

Optimize by disabling features you don’t need.

## 6) Updates/deletes: minimize write amplification

Updates are commonly “add new + delete old”, which means:
- index grows until merges reclaim deleted docs
- merge load increases with churn

Mitigations:
- reduce update frequency if possible (aggregate upstream)
- avoid patterns that repeatedly update the same logical document at high frequency
- consider separating “hot changing” fields from “mostly static” fields at the application/schema level when feasible

## 7) Commit and refresh strategy (visibility vs durability)

Lucene gives you two main levers:
- **refresh / reopen**: improves visibility to search quickly
- **commit**: improves durability by publishing a commit point

Performance implications:
- frequent commits can be expensive because they enforce durable publication
- frequent refreshes can be expensive because they create new searchers and can increase memory pressure

A common strategy in search servers is:
- refresh at a modest interval for NRT
- commit less frequently for durability (and rely on a WAL for crash recovery)

## 8) IO and filesystem considerations

Lucene performance is very sensitive to storage characteristics.
- fast SSDs typically improve flush and merge performance
- low-latency fsync can matter if you commit frequently
- sufficient disk bandwidth helps merges keep up

Also pay attention to:
- file descriptor limits (many segments imply many files)
- OS page cache behavior under mixed read/write workloads

## 9) A practical tuning checklist

If indexing is slow:
1. Confirm whether bottleneck is CPU (analysis) or IO (flush/merge).
2. Reduce segment churn (larger buffers, better batching).
3. Ensure merges can keep up (tune merge settings, provision IO).
4. Disable unneeded field features (positions, offsets, norms, stored fields).
5. Re-evaluate update/delete patterns.

If search latency degrades while indexing:
1. Check segment count and merge backlog.
2. Reduce refresh frequency if it’s overly aggressive.
3. Improve merge throughput (IO, scheduler), but beware of starving search threads.
