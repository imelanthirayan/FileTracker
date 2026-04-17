"""Change detection — compares current filesystem scan against previous scan state."""

from file_tracker.hasher import compute_file_hash
from file_tracker.logger import get_logger

def detect_changes(current_fs: dict, previous_scan_data: dict | None) -> tuple[dict, dict]:
    """Detect new, modified, pending, carried-forward, and deleted files.

    Args:
        current_fs: Dict from scanner — {abs_path: {"mtime": ..., "size": ...}}
        previous_scan_data: Full previous scan JSON dict, or None for first run.

    Returns:
        (files_dict, counts) where:
        - files_dict: Complete files mapping for the new scan JSON.
        - counts: {"new": N, "modified": N, "pending": N, "carried_forward": N, "deleted": N}
    """
    log = get_logger()
    prev_files = {}
    if previous_scan_data is not None:
        prev_files = previous_scan_data.get("files", {})

    files: dict = {}
    counts = {"new": 0, "modified": 0, "pending": 0, "carried_forward": 0, "deleted": 0}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    # Process files currently on disk
    for path, fs_info in current_fs.items():
        prev_entry = prev_files.get(path)

        if prev_entry is None:
            # New file — not in previous scan
            try:
                sha = compute_file_hash(path)
            except (PermissionError, FileNotFoundError, OSError) as e:
                log.warning("Cannot hash new file, skipping: %s — %s", path, e)
                continue

            files[path] = {
                "mtime": fs_info["mtime"],
                "size": fs_info["size"],
                "sha256": sha,
                "status": "pending",
                "reason": "new",
                "first_seen": now,
                "last_modified": now,
                "processed_at": None,
            }
            counts["new"] += 1
            log.debug("New file: %s", path)

        elif fs_info["mtime"] != prev_entry.get("mtime"):
            # mtime changed — hash to confirm actual content change
            try:
                sha = compute_file_hash(path)
            except (PermissionError, FileNotFoundError, OSError) as e:
                log.warning("Cannot hash modified file, skipping: %s — %s", path, e)
                continue

            if sha != prev_entry.get("sha256"):
                # Content actually changed — reset to pending
                files[path] = {
                    "mtime": fs_info["mtime"],
                    "size": fs_info["size"],
                    "sha256": sha,
                    "status": "pending",
                    "reason": "modified",
                    "first_seen": prev_entry.get("first_seen", now),
                    "last_modified": now,
                    "processed_at": None,
                }
                counts["modified"] += 1
                log.debug("Modified file: %s", path)
            else:
                # mtime changed but content identical (e.g., touch) — keep previous status
                files[path] = {
                    "mtime": fs_info["mtime"],
                    "size": fs_info["size"],
                    "sha256": sha,
                    "status": prev_entry.get("status", "pending"),
                    "reason": "carried_forward" if prev_entry.get("status") == "processed" else "pending",
                    "first_seen": prev_entry.get("first_seen", now),
                    "last_modified": prev_entry.get("last_modified", now),
                    "processed_at": prev_entry.get("processed_at"),
                }
                if prev_entry.get("status") == "processed":
                    counts["carried_forward"] += 1
                else:
                    counts["pending"] += 1

        elif prev_entry.get("status") == "pending":
            # No mtime change, still pending from last time — carry forward
            files[path] = {
                "mtime": fs_info["mtime"],
                "size": fs_info["size"],
                "sha256": prev_entry.get("sha256", ""),
                "status": "pending",
                "reason": prev_entry.get("reason", "carried_forward"),
                "first_seen": prev_entry.get("first_seen", now),
                "last_modified": prev_entry.get("last_modified", now),
                "processed_at": prev_entry.get("processed_at"),
            }
            counts["pending"] += 1

        elif prev_entry.get("status") == "processed":
            # No mtime change, already processed — carry forward
            files[path] = {
                "mtime": fs_info["mtime"],
                "size": fs_info["size"],
                "sha256": prev_entry.get("sha256", ""),
                "status": "processed",
                "reason": "carried_forward",
                "first_seen": prev_entry.get("first_seen", now),
                "last_modified": prev_entry.get("last_modified", now),
                "processed_at": prev_entry.get("processed_at"),
            }
            counts["carried_forward"] += 1

    # Detect deleted files
    for path in prev_files:
        if path not in current_fs:
            files[path] = {
                **prev_files[path],
                "status": "deleted",
                "reason": "deleted",
                "last_modified": now,
            }
            counts["deleted"] += 1

    return files, counts
