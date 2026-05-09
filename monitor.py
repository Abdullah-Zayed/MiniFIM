
import threading
import time
import json
import os
from datetime import datetime

from utils import scan_directory, get_file_info, sha256_hash


class FileMonitor:
    """
    Monitors a directory for file integrity changes by comparing
    periodic scans against a stored baseline.
    """

    def __init__(self, baseline_file="fim_baseline.json"):
        self.baseline = {}
        self.baseline_file = baseline_file
        self.target_directory = None
        self.monitoring = False
        self.scan_interval = 3  
        self.exclusion_patterns = []
        self._thread = None
        self._on_event = None  
        self._scan_count = 0
        self._total_changes = 0
        self._start_time = None

    def set_event_callback(self, callback):
        """Set callback function for file events: callback(event_type, filepath, details)"""
        self._on_event = callback

    def set_directory(self, directory):
        """Set the directory to monitor."""
        self.target_directory = directory

    def set_scan_interval(self, seconds):
        """Set the polling interval in seconds."""
        self.scan_interval = max(1, min(60, seconds))

    def set_exclusion_patterns(self, patterns):
        """Set list of glob patterns to exclude from monitoring."""
        self.exclusion_patterns = patterns

    def _emit(self, event_type, filepath="", details=None):
        """Emit an event through the callback."""
        if self._on_event:
            self._on_event(event_type, filepath, details or {})

    def build_baseline(self):
        """Scan directory and create the initial baseline snapshot."""
        if not self.target_directory:
            return

        self.baseline = scan_directory(self.target_directory, self.exclusion_patterns)

        # Save baseline to disk
        try:
            with open(self.baseline_file, "w") as f:
                json.dump(self.baseline, f, indent=2)
        except OSError:
            pass

        self._emit("baseline_built", details={
            "file_count": len(self.baseline),
            "directory": self.target_directory,
        })

    def start(self):
        """Start monitoring in a background thread."""
        if not self.target_directory or self.monitoring:
            return

        self.build_baseline()
        self.monitoring = True
        self._scan_count = 0
        self._total_changes = 0
        self._start_time = time.time()

        self._emit("monitoring_started", details={
            "directory": self.target_directory,
            "interval": self.scan_interval,
        })

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
        self._emit("monitoring_stopped", details={
            "scans_completed": self._scan_count,
            "total_changes": self._total_changes,
        })

    def _monitor_loop(self):
        """Main monitoring loop — runs in background thread."""
        while self.monitoring:
            time.sleep(self.scan_interval)
            if not self.monitoring:
                break
            self._perform_scan()

    def _perform_scan(self):
        """Perform a single scan cycle and compare against baseline."""
        self._scan_count += 1
        current_files = scan_directory(self.target_directory, self.exclusion_patterns)
        changes_in_scan = 0

        # Check for new and modified files
        for path, current_hash in current_files.items():
            if path not in self.baseline:
                # New file detected
                info = get_file_info(path)
                self._emit("file_created", path, {
                    "hash": current_hash,
                    "size": info["size"],
                    "modified": info["modified"],
                })
                changes_in_scan += 1

            elif self.baseline[path] != current_hash:
                # File modified
                info = get_file_info(path)
                self._emit("file_modified", path, {
                    "old_hash": self.baseline[path],
                    "new_hash": current_hash,
                    "size": info["size"],
                    "modified": info["modified"],
                })
                changes_in_scan += 1

        # Check for deleted files
        for path in self.baseline:
            if path not in current_files:
                self._emit("file_deleted", path, {
                    "old_hash": self.baseline[path],
                })
                changes_in_scan += 1

        self._total_changes += changes_in_scan
        # Update baseline to current state
        self.baseline = current_files

    @property
    def file_count(self):
        """Number of files currently in baseline."""
        return len(self.baseline)

    @property
    def scan_count(self):
        """Number of scans completed."""
        return self._scan_count

    @property
    def total_changes(self):
        """Total changes detected across all scans."""
        return self._total_changes

    @property
    def uptime_seconds(self):
        """Seconds since monitoring started."""
        if self._start_time:
            return int(time.time() - self._start_time)
        return 0

    @property
    def uptime_formatted(self):
        """Human-readable uptime string."""
        s = self.uptime_seconds
        if s < 60:
            return f"{s}s"
        elif s < 3600:
            return f"{s // 60}m {s % 60}s"
        else:
            return f"{s // 3600}h {(s % 3600) // 60}m"
