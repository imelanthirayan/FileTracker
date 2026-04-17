"""Scan JSON I/O, status management, and TrackerSession for batch operations."""

import json
import os
import tempfile
from datetime import datetime, timezone

from file_tracker.config import load_config
from file_tracker.logger import get_logger

def find_latest_scan(scans_dir: str) -> str | None:
    """Find the most recent scan JSON file in the scans directory."""
    if not os.path.isdir(scans_dir):
        return None

    scan_files = sorted(
        [f for f in os.listdir(scans_dir) if f.startswith("scan_") and f.endswith(".json")],
        reverse=True,
    )
    if not scan_files:
        return None
    return os.path.join(scans_dir, scan_files[0])

def load_scan(scan_path: str) -> dict:
    """Load a scan JSON file and return parsed data."""
    with open(scan_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _atomic_write_json(filepath: str, data: dict) -> None:
    """Write JSON atomically via temp file + rename."""
    dir_path = os.path.dirname(filepath)
    os.makedirs(dir_path, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, filepath)
    except BaseException:
        os.unlink(tmp_path)
        raise

def save_scan(scans_dir: str, scan_data: dict) -> str:
    """Write a new scan JSON file atomically. Returns the file path."""
    os.makedirs(scans_dir, exist_ok=True)
    scan_id = scan_data.get("scan_id", f"scan_{_now_id()}")
    filepath = os.path.join(scans_dir, f"{scan_id}.json")
    _atomic_write_json(filepath, scan_data)
    return filepath

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")

def _normalize_paths(file_paths) -> list[str]:
    """Accept a single string or list of strings, normalize all to realpath."""
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    return [os.path.realpath(p) for p in file_paths]

# ---------------------------------------------------------------------------
# Standalone convenience functions (load JSON per call)
# ---------------------------------------------------------------------------

def mark_processed(config_path: str, file_paths) -> dict:
    """Mark files as processed in the latest scan JSON.

    Args:
        config_path: Path to config.yaml.
        file_paths: Single file path string or list of file path strings.

    Returns:
        {"updated": [...], "not_found": [...]}
    """
    config = load_config(config_path)
    log = get_logger()
    scan_path = find_latest_scan(config["scans_dir"])

    if scan_path is None:
        log.warning("No scan JSON found — run a scan first")
        return {"updated": [], "not_found": _normalize_paths(file_paths)}

    scan_data = load_scan(scan_path)
    files = scan_data.get("files", {})
    paths = _normalize_paths(file_paths)
    now = _now_iso()

    updated = []
    not_found = []
    for path in paths:
        if path in files and files[path]["status"] != "processed":
            files[path]["status"] = "processed"
            files[path]["processed_at"] = now
            updated.append(path)
        else:
            not_found.append(path)

    # Recalculate summary
    pending = sum(1 for v in files.values() if v.get("status") == "pending")
    processed_count = sum(1 for v in files.values() if v.get("status") == "processed")
    deleted = sum(1 for v in files.values() if v.get("status") == "deleted")
    scan_data["summary"].update({
        "total_files": len(files),
        "pending": pending,
        "processed": processed_count,
        "deleted": deleted,
    })
    # Save updated scan
    scan_data["files"] = files
    _atomic_write_json(scan_path, scan_data)
    return {"updated": updated, "not_found": not_found}

def get_pending_files(config_path: str) -> list[str]:
    """Return list of files with status 'pending' in the latest scan."""
    config = load_config(config_path)
    scan_path = find_latest_scan(config["scans_dir"])
    if scan_path is None:
        return []
    scan_data = load_scan(scan_path)
    return [p for p, v in scan_data.get("files", {}).items() if v.get("status") == "pending"]

def get_status(config_path: str, file_path: str = None):
    """Return summary or file status from the latest scan."""
    config = load_config(config_path)
    scan_path = find_latest_scan(config["scans_dir"])
    if scan_path is None:
        return None
    scan_data = load_scan(scan_path)
    if file_path:
        abs_path = os.path.realpath(file_path)
        return scan_data.get("files", {}).get(abs_path)
    return {
        "scan_id": scan_data.get("scan_id"),
        "scan_timestamp": scan_data.get("scan_timestamp"),
        **scan_data.get("summary", {}),
    }

class TrackerSession:
    """Batch context manager for marking files as processed."""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._pending = get_pending_files(config_path)
        self._marked = []
    def mark(self, file_path: str):
        if file_path in self._pending:
            mark_processed(self.config_path, [file_path])
            self._marked.append(file_path)
    def get_marked(self):
        return self._marked
