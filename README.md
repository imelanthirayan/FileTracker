

# File Tracker

**Easily keep track of new and changed files in your folders.**

File Tracker is a simple tool that helps you know exactly which files are new, which have changed, and which have already been processed. This means you never miss an update, and you don’t waste time re-processing files that haven’t changed.

---


## Where can you use it?

File Tracker is especially useful in technical and AI-driven projects, including:

- **RAG (Retrieval-Augmented Generation) pipelines:** Detect new or updated documents to trigger vector database refreshes, ensuring your LLMs always have access to the latest knowledge.
- **LLM data ingestion:** Automate the process of finding and processing only changed files for embedding, chunking, or indexing.
- **Vector database updates:** Efficiently manage which files need to be re-embedded and pushed to Pinecone, Weaviate, Qdrant, or other vector stores.
- **Automated document ingestion:** Integrate with ETL or data lake workflows to avoid redundant processing and keep your knowledge base up to date.
- **Content refresh for chatbots and search:** Ensure only new or modified content is re-indexed for semantic search or conversational AI.
- **General data pipelines:** Any workflow where you need to track file status and avoid double-processing in large-scale, automated systems.

If your project involves RAG, LLMs, or any automated data/document pipeline, File Tracker helps you keep everything efficient and up to date!

---

**Easily keep track of new and changed files in your folders.**

File Tracker is a simple tool that helps you know exactly which files are new, which have changed, and which have already been processed. This means you never miss an update, and you don’t waste time re-processing files that haven’t changed.


**Who can use it?**
- **Researchers:** Track which research papers or datasets are new or updated in your folders.
- **Data teams:** Automate data ingestion by only processing new or changed files.
- **Content managers:** Know which articles, images, or documents need review or publishing.
- **Developers:** Integrate with data pipelines or ETL jobs to avoid redundant work.
- **Educators:** Manage and track assignments or resources in shared folders.

Anyone who works with lots of documents, data files, or needs to automate file processing can benefit from File Tracker.

**What does it do?**
- Watches your folders and remembers the status of every file.
- Shows you what’s new, what’s changed, and what’s done.
- Lets you mark files as “processed” so you can focus only on what’s next.

**Why use it?**
- Avoids double work—never process the same file twice unless it’s changed.
- Saves time and reduces mistakes in data and document workflows.



*Technical summary:* File Tracker is a reusable file change detector for data and document pipelines. It scans configured folders, detects new or modified files using modification time and SHA-256 hashing, and tracks per-file processing status so your pipeline only processes what’s changed.

## Quick Start

```bash
# Install into your project's venv
pip install -e /path/to/file-tracker

# Or just install dependencies if copying the folder
pip install pyyaml
```
---
## Troubleshooting

- **Config file not found:** Ensure the path to `config.yaml` is correct and the file exists.
- **Source folder does not exist:** Check that all `source_folders` in your config exist and are accessible.
- **Permission denied:** Run with appropriate permissions if scanning protected folders.
- **CLI not found after install:** Make sure your virtual environment is activated and run `pip install -e .` from the project root.

If you encounter other issues, check the logs in `data/logs/file_tracker.log` or open an issue.
```

### 1. Configure

Edit `config.yaml` with your folder paths:

```yaml
source_folders:
  - /path/to/your/documents
  - /path/to/your/data
  - /another/folder/to/watch

scans_dir: ./data/scans

exclude_patterns:
  - "*.pyc"
  - "__pycache__"
  - ".DS_Store"
  - ".git"
  - ".venv"
  - "*.tmp"

log_level: INFO
```

### 2. Run a Scan

```bash
file-tracker scan --config config.yaml
```

Output:

```
Scan JSON: ./data/scans/scan_2026-04-14T10-00-00.json
Total files:  150
  Pending:    150
  Processed:  0
  Deleted:    0
  New:        150
  Modified:   0
```

### 3. Check Status

```bash
file-tracker status --config config.yaml
file-tracker status --config config.yaml --file /path/to/specific/file.pdf
```

### 4. List Pending Files

```bash
file-tracker pending --config config.yaml
file-tracker pending --config config.yaml --json    # Output as JSON array
```

### 5. Mark Files as Processed

```bash
# Mark specific files
file-tracker mark-processed --config config.yaml --files /path/file1.pdf /path/file2.docx

# Mark ALL pending files at once
file-tracker mark-processed --config config.yaml --all
```

### 6. View Logs

```bash
# Last 50 entries (default)
file-tracker logs --config config.yaml

# Filter by level
file-tracker logs --config config.yaml --level WARNING
file-tracker logs --config config.yaml --level ERROR

# Control how many entries to show
file-tracker logs --config config.yaml --last 100

# Output as JSON
file-tracker logs --config config.yaml --json
```

### CLI Reference

| Command | Description |
|---------|-------------|
| `scan` | Scan folders and detect new/modified files |
| `status` | Show summary or single file status from latest scan |
| `pending` | List files that need processing |
| `mark-processed` | Mark files as processed (`--files` or `--all`) |
| `logs` | View log entries (`--level`, `--last`, `--json`) |

All commands accept `--config config.yaml` (defaults to `config.yaml` in current directory).

---

## Python API

Five functions + one session class for high-performance batch operations.

### Basic Usage

```python
from file_tracker import run_scan, get_pending_files, mark_processed, get_status, get_logs

# 1. Scan for changes
scan_path, summary = run_scan("config.yaml")
print(f"{summary['pending']} files to process")

# 2. Get files that need processing
pending = get_pending_files("config.yaml")
# Returns: ["/abs/path/file1.pdf", "/abs/path/file2.docx", ...]

# 3. Process them in your RAG pipeline
for file_path in pending:
    embed_into_vector_db(file_path)  # your code

# 4. Mark as processed — single file or batch
mark_processed("config.yaml", "/abs/path/file1.pdf")           # single
mark_processed("config.yaml", ["/abs/path/file1.pdf", "..."])   # batch

# 5. Check status
summary = get_status("config.yaml")
# Returns: {"pending": 0, "processed": 150, "deleted": 0, "total": 150, ...}

file_info = get_status("config.yaml", "/abs/path/file1.pdf")
# Returns: {"status": "processed", "sha256": "...", "mtime": ..., ...}

# 6. Read logs programmatically
errors = get_logs("config.yaml", level="ERROR", last_n=20)
warnings = get_logs("config.yaml", level="WARNING")
all_logs = get_logs("config.yaml", last_n=100)
# Returns: [{"timestamp": "...", "level": "WARNING", "module": "scanner", "message": "..."}]
```

### High-Performance: TrackerSession

For large-scale operations (10K-100K+ files), use `TrackerSession` to avoid repeated disk I/O:

```python
from file_tracker import TrackerSession

with TrackerSession("config.yaml") as session:
    # All reads are in-memory — zero disk I/O per call
    pending = session.get_pending_files()

    for f in pending:
        embed_into_vector_db(f)
        session.mark_processed(f)  # in-memory update, no disk write

    status = session.get_status()
    # Writes to disk ONCE on exit (only if something changed)
```

| Operation | Without session | With TrackerSession |
|-----------|----------------|---------------------|
| Load JSON | Once per function call | **Once on entry** |
| mark_processed per file | Read + write each time | **In-memory, 0 I/O** |
| Save JSON | Once per function call | **Once on exit** |

---

## How It Works

### First Run
1. Scans all configured folders recursively
2. Every file is added with status `"pending"`
3. Writes a scan JSON to `data/scans/`

### Subsequent Runs
1. Reads the latest scan JSON (including any `"processed"` updates)
2. Scans filesystem and compares:
   - **New files** (not in previous scan) → `"pending"`
   - **Modified files** (mtime changed + SHA-256 hash differs) → reset to `"pending"`
   - **Touched files** (mtime changed but hash identical) → keeps previous status
   - **Still pending** (never marked processed) → carried forward as `"pending"`
   - **Processed + unmodified** → carried forward as `"processed"` (skipped)
   - **Deleted from disk** → marked `"deleted"`
3. Writes a NEW scan JSON

### Change Detection
Uses a two-phase approach for accuracy + speed:
1. **mtime filter** (fast) — only files with changed modification times are candidates
2. **SHA-256 hash** (accurate) — confirms actual content change, avoiding false positives from `touch`

---

## Scan JSON Schema

Each scan produces a self-contained JSON file in `data/scans/`:

```json
{
  "version": 1,
  "scan_id": "scan_2026-04-14T10-00-00",
  "scan_timestamp": "2026-04-14T10:00:00",
  "previous_scan_id": "scan_2026-04-13T10-00-00",
  "source_folders": ["/path/to/documents"],
  "files": {
    "/abs/path/to/file.pdf": {
      "mtime": 1713100000.0,
      "size": 12345,
      "sha256": "a1b2c3...",
      "status": "processed",
      "reason": "carried_forward",
      "first_seen": "2026-04-13T10:00:00",
      "last_modified": "2026-04-13T10:00:00",
      "processed_at": "2026-04-13T11:00:00"
    },
    "/abs/path/to/new_file.docx": {
      "mtime": 1713200000.0,
      "size": 6789,
      "sha256": "d4e5f6...",
      "status": "pending",
      "reason": "new",
      "first_seen": "2026-04-14T10:00:00",
      "last_modified": "2026-04-14T10:00:00",
      "processed_at": null
    },
  }
  ```


| Status | Meaning |
|--------|---------|
| `pending` | Needs processing by RAG pipeline |
| `processed` | Successfully processed, will be skipped unless modified |
| `deleted` | File was removed from disk since last scan |

### Reason Values

| Reason | Meaning |
|--------|---------|
| `new` | File discovered for the first time this scan |
| `modified` | File content changed since last scan (hash differs) |
| `pending` | Carried forward — was pending in previous scan, still unprocessed |
| `carried_forward` | Was processed and hasn't changed — no action needed |
| `deleted` | File no longer exists on disk |

---

## Configuration Reference

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `source_folders` | Yes | — | List of absolute folder paths to scan |
| `scans_dir` | No | `./data/scans` | Where scan JSON files are stored |
| `exclude_patterns` | No | `[]` | Glob patterns for files/folders to skip |
| `log_level` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

---

## Logging

Logs are written to both **console** and a **rotating log file**:
- **File**: `data/logs/file_tracker.log`
- **Rotation**: 5 MB max per file, 3 backup files kept

### Reading Logs Programmatically

```python
from file_tracker import get_logs

# All recent logs
logs = get_logs("config.yaml")

# Only warnings
warnings = get_logs("config.yaml", level="WARNING")

# Last 100 error entries
errors = get_logs("config.yaml", level="ERROR", last_n=100)

# Each entry is a dict:
# {"timestamp": "2026-04-14 10:00:05", "level": "WARNING",
#  "module": "file_tracker.scanner", "message": "Permission denied: /path/..."}
```

---

## Reusability

This package is designed to be copied into any project:

1. Copy the `file_tracker/` folder into your project
2. Edit `config.yaml` with your folder paths
3. Install: `pip install -e .` (or just `pip install pyyaml`)
4. Run: `file-tracker scan --config config.yaml`

Each project gets its own `config.yaml`, `data/scans/`, and `data/logs/` — completely independent.
