import os

_PLYER_AVAILABLE = False
try:
    from plyer import notification as plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    pass


class Notifier:

    def __init__(self, enabled=True):
        self.enabled = enabled and _PLYER_AVAILABLE
        self._app_name = "MiniFIM"

    @property
    def available(self):
        return _PLYER_AVAILABLE

    def toggle(self, enabled):
        self.enabled = enabled and _PLYER_AVAILABLE

    def notify(self, title, message, severity="INFO"):
        if not self.enabled:
            return
        if severity not in ("WARNING", "CRITICAL"):
            return
        try:
            plyer_notification.notify(
                title=f"🛡️ {self._app_name} — {title}",
                message=message[:256],
                app_name=self._app_name,
                timeout=8 if severity == "CRITICAL" else 5,
            )
        except Exception:
            pass

    def notify_file_event(self, event_type, filepath):
        basename = os.path.basename(filepath)
        titles = {
            "file_created": "New File Detected",
            "file_modified": "File Modified",
            "file_deleted": "File Deleted",
        }
        severities = {
            "file_created": "WARNING",
            "file_modified": "WARNING",
            "file_deleted": "CRITICAL",
        }
        title = titles.get(event_type, "Alert")
        severity = severities.get(event_type, "INFO")
        self.notify(title, f"{basename}\n{filepath}", severity)
