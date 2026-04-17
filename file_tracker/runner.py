"""Orchestrator — ties together config, scanning, detection, and state persistence."""

from datetime import datetime, timezone

from file_tracker.config import load_config
from file_tracker.detector import detect_changes
from file_tracker.logger import setup_logging, get_logger
from file_tracker.scanner import scan_folders
from file_tracker.state import find_latest_scan, load_scan, save_scan

def run_scan(config_path: str) -> tuple[str, dict]:
    """Run a full scan: load config, scan folders, detect changes, write scan JSON.

    Args:
        config_path: Path to config.yaml.

    Returns:
        (scan_json_path, summary_dict)
    """
    config = load_config(config_path)
    setup_logging(config)
    log = get_logger()

    log.info("=== File Tracker — Scan Started ===")
    log.info("Config: %s", config["config_path"])
    log.info("Source folders: %s", config["source_folders"])

    # 1. Scan filesystem
    current_fs = scan_folders(config["source_folders"], config["exclude_patterns"])

    # 2. Load previous scan (if any)
    prev_scan_path = find_latest_scan(config["scans_dir"])
    previous_scan_data = None
    previous_scan_id = None

    if prev_scan_path is not None:
        previous_scan_data = load_scan(prev_scan_path)
        previous_scan_id = previous_scan_data.get("scan_id")
        log.info("Previous scan loaded: %s", previous_scan_id)
    else:
        log.info("No previous scan found — this is the first run")

    # 3. Detect changes
    files, counts = detect_changes(current_fs, previous_scan_data)

    # 4. Build scan data
    now = datetime.now(timezone.utc)
    scan_id = f"scan_{now.strftime('%Y-%m-%dT%H-%M-%S')}"

    pending = sum(1 for v in files.values() if v.get("status") == "pending")
    processed = sum(1 for v in files.values() if v.get("status") == "processed")
    deleted = sum(1 for v in files.values() if v.get("status") == "deleted")

    scan_data = {
        "version": 1,
        "scan_id": scan_id,
        "scan_timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "previous_scan_id": previous_scan_id,
        "source_folders": config["source_folders"],
        "files": files,
        "summary": {
            "total_files": len(files),
            "pending": pending,
            "processed": processed,
            "deleted": deleted,
            "new_this_scan": counts["new"],
            "modified_this_scan": counts["modified"],
        },
    }

    # 5. Save scan JSON
    scan_path = save_scan(config["scans_dir"], scan_data)

    summary = scan_data["summary"]
    log.info("Scan JSON written: %s", scan_path)
    log.info(
        "Summary — total: %d, pending: %d, processed: %d, deleted: %d, "
        "new: %d, modified: %d",
        summary["total_files"], summary["pending"], summary["processed"],
        summary["deleted"], summary["new_this_scan"], summary["modified_this_scan"],
    )
    log.info("=== Scan Complete ===")

    return scan_path, summary
