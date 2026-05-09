import hashlib
import csv
import os
import fnmatch
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def sha256_hash(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for block in iter(lambda: f.read(8192), b""):
                h.update(block)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def get_file_info(filepath):
    try:
        stat = os.stat(filepath)
        return {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }
    except (OSError, PermissionError):
        return {"size": 0, "modified": "Unknown"}


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def should_exclude(filepath, patterns):
    basename = os.path.basename(filepath)
    for pattern in patterns:
        pattern = pattern.strip()
        if not pattern:
            continue
        if fnmatch.fnmatch(basename, pattern):
            return True
        if fnmatch.fnmatch(filepath, pattern):
            return True
        normalized = filepath.replace("\\", "/")
        if fnmatch.fnmatch(normalized, f"*/{pattern}"):
            return True
    return False


def export_logs_to_csv(log_entries, output_path):
    fieldnames = ["Timestamp", "Severity", "Event Type", "File Path", "Details"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in log_entries:
            writer.writerow({
                "Timestamp": entry.get("timestamp", ""),
                "Severity": entry.get("severity", ""),
                "Event Type": entry.get("event_type", ""),
                "File Path": entry.get("filepath", ""),
                "Details": entry.get("details", ""),
            })
    return output_path


def scan_directory(directory, exclusion_patterns=None, max_workers=8):
    if exclusion_patterns is None:
        exclusion_patterns = []

    file_paths = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            if not should_exclude(path, exclusion_patterns):
                file_paths.append(path)

    file_hashes = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(sha256_hash, p): p for p in file_paths}
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                h = future.result()
                if h:
                    file_hashes[path] = h
            except Exception:
                pass
    return file_hashes
