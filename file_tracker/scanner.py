"""Recursive folder scanning with exclusion, symlink safety, and error handling."""

import os
from fnmatch import fnmatch

from file_tracker.logger import get_logger

def _is_excluded(name: str, exclude_patterns: list[str]) -> bool:
    """Check if a file or directory name matches any exclusion pattern."""
    return any(fnmatch(name, pat) for pat in exclude_patterns)

def scan_folders(folders: list[str], exclude_patterns: list[str] | None = None) -> dict:
    """Recursively scan folders and return file metadata.

    Args:
        folders: List of absolute folder paths to scan.
        exclude_patterns: Glob patterns to exclude (matched against basename).

    Returns:
        Dict keyed by canonical absolute file path:
        {"/abs/path/file.pdf": {"mtime": 1713100000.0, "size": 12345}}
    """
    log = get_logger()
    exclude_patterns = exclude_patterns or []
    result: dict = {}

    for folder in folders:
        folder = os.path.realpath(folder)
        if not os.path.isdir(folder):
            log.warning("Source folder does not exist, skipping: %s", folder)
            continue

        log.info("Scanning folder: %s", folder)

        for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
            # Filter out excluded directories in-place (prevents os.walk from descending)
            dirnames[:] = [
                d for d in dirnames
                if not _is_excluded(d, exclude_patterns)
                and not os.path.islink(os.path.join(dirpath, d))
            ]

            for filename in filenames:
                if _is_excluded(filename, exclude_patterns):
                    continue

                filepath = os.path.join(dirpath, filename)

                # Skip symlinks
                if os.path.islink(filepath):
                    log.debug("Skipping symlink: %s", filepath)
                    continue

                # Normalize path
                filepath = os.path.realpath(filepath)

                # Skip duplicates (can happen with overlapping source_folders)
                if filepath in result:
                    continue

                try:
                    stat = os.stat(filepath)
                    result[filepath] = {
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                    }
                except PermissionError:
                    log.warning("Permission denied, skipping: %s", filepath)
                except FileNotFoundError:
                    log.warning("File disappeared during scan, skipping: %s", filepath)
                except OSError as e:
                    log.warning("OS error reading file, skipping: %s — %s", filepath, e)

    log.info("Scan complete: %d files found", len(result))
    return result
