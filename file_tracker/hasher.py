"""SHA-256 file hashing with chunked reads for large file safety."""

import hashlib

_CHUNK_SIZE = 8192  # 8 KB

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file, reading in chunks."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()
