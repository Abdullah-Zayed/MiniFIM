import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
from datetime import datetime
from theme import *
from monitor import FileMonitor
from notifier import Notifier
from utils import export_logs_to_csv, format_file_size, get_file_info

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MiniFIMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MiniFIM — File Integrity Monitor")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(900, 600)
        self.configure(fg_color=BG_PRIMARY)
        self.monitor = FileMonitor()
        self.monitor.set_event_callback(self._on_monitor_event)
        self.notifier = Notifier(enabled=True)
        self.log_entries = []
        self._pulse_state = False
        self._current_view = "monitor"
        self._build_layout()
        self._start_dashboard_updater()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._content = ctk.CTkFrame(self, fg_color=BG_PRIMARY, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(2, weight=1)
        self._content.grid_columnconfigure(0, weight=1)
        self._build_dashboard()
        self._build_controls()
        self._build_log_area()
        self._build_detail_panel()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, fg_color=BG_SECONDARY, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 8))
        ctk.CTkLabel(logo_frame, text="🛡️", font=(FONT_FAMILY, 28)).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="MiniFIM", font=FONT_TITLE, text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="File Integrity Monitor", font=FONT_TINY, text_color=TEXT_SECONDARY).pack(anchor="w")
        sep = ctk.CTkFrame(sb, height=1, fg_color=BORDER)
        sep.pack(fill="x", padx=16, pady=12)
        self._nav_btns = {}
        FONT_NAV = (FONT_FAMILY, 15, "bold")
        nav_items = [("📊", "Monitor", "monitor"), ("📋", "Baseline", "baseline"), ("⚙️", "Settings", "settings")]
        for icon, label, view in nav_items:
            btn = ctk.CTkButton(sb, text=f"  {icon}  {label}", font=FONT_NAV, anchor="w",
                                fg_color="transparent", hover_color=BG_TERTIARY, text_color=TEXT_PRIMARY,
                                height=50, corner_radius=BUTTON_CORNER_RADIUS,
                                command=lambda v=view: self._switch_view(v))
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_btns[view] = btn
        self._nav_btns["monitor"].configure(fg_color=BG_TERTIARY)
        bottom = ctk.CTkFrame(sb, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=16, pady=16)
        self._status_dot = ctk.CTkLabel(bottom, text="●", font=(FONT_FAMILY, 16), text_color=STATUS_INACTIVE)
        self._status_dot.pack(side="left")
        self._status_label = ctk.CTkLabel(bottom, text=" Stopped", font=FONT_SMALL, text_color=TEXT_SECONDARY)
        self._status_label.pack(side="left", padx=(4, 0))

    def _build_dashboard(self):
        dash = ctk.CTkFrame(self._content, fg_color="transparent")
        dash.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        self._dash_frame = dash
        for i in range(4):
            dash.grid_columnconfigure(i, weight=1)
        self._stat_cards = {}
        stats = [("Files Monitored", "0", ACCENT_CYAN), ("Changes Detected", "0", ACCENT_YELLOW),
                 ("Scan Interval", "3s", ACCENT_PURPLE), ("Uptime", "0s", ACCENT_GREEN)]
        for i, (label, val, color) in enumerate(stats):
            card = ctk.CTkFrame(dash, fg_color=BG_CARD, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=BORDER)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            ctk.CTkLabel(card, text=label, font=FONT_STAT_LABEL, text_color=TEXT_SECONDARY).pack(anchor="w", padx=14, pady=(12, 0))
            val_lbl = ctk.CTkLabel(card, text=val, font=FONT_STAT_VALUE, text_color=color)
            val_lbl.pack(anchor="w", padx=14, pady=(0, 12))
            self._stat_cards[label] = val_lbl

    def _build_controls(self):
        ctrl = ctk.CTkFrame(self._content, fg_color="transparent")
        ctrl.grid(row=1, column=0, sticky="ew", padx=20, pady=(4, 4))
        self._path_label = ctk.CTkLabel(ctrl, text="No folder selected", font=FONT_SMALL, text_color=TEXT_SECONDARY)
        self._path_label.pack(side="left")
        self._export_btn = ctk.CTkButton(ctrl, text="📤 Export CSV", font=FONT_SMALL, width=110, height=32,
                                          fg_color=BG_TERTIARY, hover_color=BORDER, text_color=TEXT_PRIMARY,
                                          corner_radius=BUTTON_CORNER_RADIUS, command=self._export_csv)
        self._export_btn.pack(side="right", padx=(6, 0))
        self._clear_btn = ctk.CTkButton(ctrl, text="🗑️ Clear Log", font=FONT_SMALL, width=100, height=32,
                                         fg_color=BG_TERTIARY, hover_color=BORDER, text_color=TEXT_PRIMARY,
                                         corner_radius=BUTTON_CORNER_RADIUS, command=self._clear_log)
        self._clear_btn.pack(side="right", padx=(6, 0))
        self._stop_btn = ctk.CTkButton(ctrl, text="⏹  Stop", font=FONT_BUTTON, width=100, height=BUTTON_HEIGHT,
                                        fg_color=ACCENT_RED, hover_color="#da3633", text_color="white",
                                        corner_radius=BUTTON_CORNER_RADIUS, state="disabled", command=self._stop)
        self._stop_btn.pack(side="right", padx=(6, 0))
        self._start_btn = ctk.CTkButton(ctrl, text="▶  Start", font=FONT_BUTTON, width=100, height=BUTTON_HEIGHT,
                                         fg_color=ACCENT_GREEN, hover_color="#2ea043", text_color="white",
                                         corner_radius=BUTTON_CORNER_RADIUS, state="disabled", command=self._start)
        self._start_btn.pack(side="right", padx=(6, 0))
        self._folder_btn = ctk.CTkButton(ctrl, text="📂 Select Folder", font=FONT_BUTTON, width=140, height=BUTTON_HEIGHT,
                                          fg_color=ACCENT_CYAN, hover_color="#388bfd", text_color="white",
                                          corner_radius=BUTTON_CORNER_RADIUS, command=self._select_folder)
        self._folder_btn.pack(side="right", padx=(6, 0))

    def _build_log_area(self):
        log_frame = ctk.CTkFrame(self._content, fg_color=BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=BORDER)
        log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 4))
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(log_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        ctk.CTkLabel(header, text="Integrity Logs", font=FONT_HEADING, text_color=TEXT_PRIMARY).pack(side="left")
        self._log_text = tk.Text(log_frame, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LOG,
                                  insertbackground=TEXT_PRIMARY, selectbackground=ACCENT_CYAN,
                                  relief="flat", bd=0, padx=14, pady=8, wrap="word", cursor="arrow", state="disabled")
        self._log_text.grid(row=1, column=0, sticky="nsew", padx=2, pady=(4, 8))
        scrollbar = ctk.CTkScrollbar(log_frame, command=self._log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 4), pady=8)
        self._log_text.configure(yscrollcommand=scrollbar.set)
        self._log_text.tag_configure("INFO", foreground=ACCENT_CYAN)
        self._log_text.tag_configure("WARNING", foreground=ACCENT_YELLOW)
        self._log_text.tag_configure("CRITICAL", foreground=ACCENT_RED)
        self._log_text.tag_configure("TIMESTAMP", foreground=TEXT_MUTED)
        self._log_text.tag_configure("FILEPATH", foreground=ACCENT_PURPLE)
        self._log_message("INFO", "general", "", "MiniFIM initialized. Select a directory to begin monitoring.")

    def _build_detail_panel(self):
        self._detail_frame = ctk.CTkFrame(self._content, fg_color=BG_CARD, corner_radius=CARD_CORNER_RADIUS, height=120, border_width=1, border_color=BORDER)
        self._detail_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))
        self._detail_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self._detail_frame, text="Last Event Details", font=FONT_HEADING, text_color=TEXT_PRIMARY).grid(row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(10, 4))
        labels = ["Event:", "File:", "Hash:", "Size:"]
        self._detail_values = {}
        for i, lbl in enumerate(labels):
            ctk.CTkLabel(self._detail_frame, text=lbl, font=FONT_SMALL, text_color=TEXT_SECONDARY).grid(row=1, column=i, sticky="w", padx=(14 if i == 0 else 6), pady=(0, 10))
            val = ctk.CTkLabel(self._detail_frame, text="—", font=FONT_SMALL, text_color=TEXT_PRIMARY)
            val.grid(row=2, column=i, sticky="w", padx=(14 if i == 0 else 6), pady=(0, 10))
            self._detail_values[lbl] = val

    def _build_baseline_view(self):
        for w in self._content.winfo_children():
            w.destroy()
        self._content.grid_rowconfigure(2, weight=0)
        self._content.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self._content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        ctk.CTkLabel(header, text="📋 Baseline Files", font=FONT_TITLE, text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(header, text="🔄 Refresh", font=FONT_SMALL, width=100, height=32,
                       fg_color=ACCENT_CYAN, hover_color="#388bfd", corner_radius=BUTTON_CORNER_RADIUS,
                       command=lambda: self._switch_view("baseline")).pack(side="right")
        table_frame = ctk.CTkFrame(self._content, fg_color=BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=BORDER)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table = tk.Text(table_frame, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LOG, relief="flat", bd=0,
                         padx=14, pady=10, wrap="none", cursor="arrow", state="disabled")
        table.grid(row=0, column=0, sticky="nsew")
        sb = ctk.CTkScrollbar(table_frame, command=table.yview)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=4)
        table.configure(yscrollcommand=sb.set)
        table.tag_configure("HEADER", foreground=ACCENT_CYAN, font=(FONT_MONO, 10, "bold"))
        table.tag_configure("HASH", foreground=TEXT_SECONDARY)
        table.tag_configure("PATH", foreground=ACCENT_PURPLE)
        table.config(state="normal")
        table.insert("end", f"{'File Path':<60} {'SHA-256 Hash':<66} {'Size':>10}\n", "HEADER")
        table.insert("end", "─" * 140 + "\n")
        for path, h in self.monitor.baseline.items():
            info = get_file_info(path)
            name = os.path.basename(path)
            size = format_file_size(info["size"])
            table.insert("end", f"{name:<60} ", "PATH")
            table.insert("end", f"{h:<66} ", "HASH")
            table.insert("end", f"{size:>10}\n")
        if not self.monitor.baseline:
            table.insert("end", "\n  No baseline data. Start monitoring to build a baseline.\n")
        table.config(state="disabled")

    def _build_settings_view(self):
        for w in self._content.winfo_children():
            w.destroy()
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_rowconfigure(2, weight=0)
        header = ctk.CTkFrame(self._content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        ctk.CTkLabel(header, text="⚙️ Settings", font=FONT_TITLE, text_color=TEXT_PRIMARY).pack(side="left")
        settings = ctk.CTkFrame(self._content, fg_color=BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=BORDER)
        settings.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        ctk.CTkLabel(settings, text="Scan Interval (seconds)", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(settings, text="How often to check for file changes (1–60 seconds)", font=FONT_TINY, text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 6))
        interval_frame = ctk.CTkFrame(settings, fg_color="transparent")
        interval_frame.pack(anchor="w", padx=20, pady=(0, 16))
        self._interval_var = tk.IntVar(value=self.monitor.scan_interval)
        self._interval_label = ctk.CTkLabel(interval_frame, text=f"{self.monitor.scan_interval}s", font=FONT_BODY_BOLD, text_color=ACCENT_CYAN, width=40)
        self._interval_label.pack(side="right", padx=(10, 0))
        slider = ctk.CTkSlider(interval_frame, from_=1, to=60, number_of_steps=59, width=300,
                                variable=self._interval_var, fg_color=BG_TERTIARY, progress_color=ACCENT_CYAN,
                                button_color=ACCENT_CYAN, button_hover_color="#388bfd",
                                command=self._on_interval_change)
        slider.pack(side="left")
        sep1 = ctk.CTkFrame(settings, height=1, fg_color=BORDER)
        sep1.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(settings, text="Exclusion Patterns", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(8, 4))
        ctk.CTkLabel(settings, text="Glob patterns to ignore, one per line (e.g., *.tmp, *.log, __pycache__/*)", font=FONT_TINY, text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 6))
        self._exclusion_text = ctk.CTkTextbox(settings, height=100, fg_color=BG_TERTIARY, text_color=TEXT_PRIMARY,
                                                font=FONT_LOG, corner_radius=8, border_width=1, border_color=BORDER)
        self._exclusion_text.pack(fill="x", padx=20, pady=(0, 8))
        if self.monitor.exclusion_patterns:
            self._exclusion_text.insert("1.0", "\n".join(self.monitor.exclusion_patterns))
        ctk.CTkButton(settings, text="Save Exclusion Patterns", font=FONT_BUTTON, width=200, height=BUTTON_HEIGHT,
                       fg_color=ACCENT_CYAN, hover_color="#388bfd", corner_radius=BUTTON_CORNER_RADIUS,
                       command=self._save_exclusions).pack(anchor="w", padx=20, pady=(0, 16))
        sep2 = ctk.CTkFrame(settings, height=1, fg_color=BORDER)
        sep2.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(settings, text="Desktop Notifications", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(8, 4))
        notif_status = "Available ✓" if self.notifier.available else "Not available (install plyer)"
        ctk.CTkLabel(settings, text=notif_status, font=FONT_TINY, text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 6))
        self._notif_var = tk.BooleanVar(value=self.notifier.enabled)
        switch = ctk.CTkSwitch(settings, text="Enable desktop alerts for file changes", font=FONT_BODY,
                                text_color=TEXT_PRIMARY, variable=self._notif_var, command=self._toggle_notifications,
                                fg_color=BG_TERTIARY, progress_color=ACCENT_GREEN)
        switch.pack(anchor="w", padx=20, pady=(0, 20))

    def _switch_view(self, view):
        for key, btn in self._nav_btns.items():
            btn.configure(fg_color=BG_TERTIARY if key == view else "transparent")
        self._current_view = view
        if view == "monitor":
            for w in self._content.winfo_children():
                w.destroy()
            self._content.grid_rowconfigure(1, weight=0)
            self._content.grid_rowconfigure(2, weight=1)
            self._build_dashboard()
            self._build_controls()
            self._build_log_area()
            self._build_detail_panel()
            for entry in self.log_entries:
                self._render_log_line(entry)
        elif view == "baseline":
            self._build_baseline_view()
        elif view == "settings":
            self._build_settings_view()

    def _select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.monitor.set_directory(folder)
            display = folder if len(folder) < 50 else "..." + folder[-47:]
            self._path_label.configure(text=f"📁 {display}")
            self._start_btn.configure(state="normal")
            self._log_message("INFO", "general", "", f"Directory selected: {folder}")

    def _start(self):
        if not self.monitor.target_directory:
            return
        self._log_message("INFO", "general", "", "Building baseline & starting monitor...")
        self.monitor.start()
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._folder_btn.configure(state="disabled")
        self._status_dot.configure(text_color=STATUS_ACTIVE)
        self._status_label.configure(text=" Monitoring")
        self._start_pulse()

    def _stop(self):
        self.monitor.stop()
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._folder_btn.configure(state="normal")
        self._status_dot.configure(text_color=STATUS_INACTIVE)
        self._status_label.configure(text=" Stopped")

    def _export_csv(self):
        if not self.log_entries:
            messagebox.showinfo("Export", "No log entries to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            export_logs_to_csv(self.log_entries, path)
            self._log_message("INFO", "general", "", f"Logs exported to {path}")

    def _clear_log(self):
        self.log_entries.clear()
        if hasattr(self, '_log_text'):
            self._log_text.config(state="normal")
            self._log_text.delete("1.0", "end")
            self._log_text.config(state="disabled")

    def _on_interval_change(self, value):
        val = int(value)
        self.monitor.set_scan_interval(val)
        self._interval_label.configure(text=f"{val}s")

    def _save_exclusions(self):
        text = self._exclusion_text.get("1.0", "end").strip()
        patterns = [p.strip() for p in text.split("\n") if p.strip()]
        self.monitor.set_exclusion_patterns(patterns)
        self._log_message("INFO", "general", "", f"Exclusion patterns updated: {patterns}")

    def _toggle_notifications(self):
        self.notifier.toggle(self._notif_var.get())

    def _on_monitor_event(self, event_type, filepath, details):
        severity = EVENT_SEVERITY.get(event_type, "INFO")
        detail_str = ""
        if event_type == "baseline_built":
            detail_str = f"Baseline created for {details.get('file_count', 0)} files"
        elif event_type == "monitoring_started":
            detail_str = f"Monitoring started (interval: {details.get('interval', 3)}s)"
        elif event_type == "monitoring_stopped":
            detail_str = f"Stopped — {details.get('scans_completed', 0)} scans, {details.get('total_changes', 0)} changes"
        elif event_type == "file_created":
            detail_str = f"New file: {os.path.basename(filepath)}"
        elif event_type == "file_modified":
            detail_str = f"Modified: {os.path.basename(filepath)}"
        elif event_type == "file_deleted":
            detail_str = f"Deleted: {os.path.basename(filepath)}"
        self.after(0, self._log_message, severity, event_type, filepath, detail_str)
        self.after(0, self._update_detail_panel, event_type, filepath, details)
        if event_type in ("file_created", "file_modified", "file_deleted"):
            self.notifier.notify_file_event(event_type, filepath)

    def _log_message(self, severity, event_type, filepath, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp, "severity": severity, "event_type": event_type,
            "filepath": filepath, "details": message,
        }
        self.log_entries.append(entry)
        try:
            with open("fim_alerts.log", "a") as f:
                f.write(f"[{timestamp}] [{severity}] {message}\n")
        except OSError:
            pass
        if self._current_view == "monitor" and hasattr(self, '_log_text'):
            self._render_log_line(entry)

    def _render_log_line(self, entry):
        self._log_text.config(state="normal")
        icon = SEVERITY_ICONS.get(entry["severity"], "")
        self._log_text.insert("end", f"  {entry['timestamp']}  ", "TIMESTAMP")
        self._log_text.insert("end", f"{icon} [{entry['severity']}] ", entry["severity"])
        self._log_text.insert("end", f"{entry['details']}\n")
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _update_detail_panel(self, event_type, filepath, details):
        if not hasattr(self, '_detail_values'):
            return
        event_names = {"file_created": "Created", "file_modified": "Modified", "file_deleted": "Deleted",
                        "baseline_built": "Baseline Built", "monitoring_started": "Started", "monitoring_stopped": "Stopped"}
        self._detail_values["Event:"].configure(text=event_names.get(event_type, event_type))
        self._detail_values["File:"].configure(text=os.path.basename(filepath) if filepath else "—")
        h = details.get("new_hash", details.get("hash", details.get("old_hash", "—")))
        self._detail_values["Hash:"].configure(text=h[:20] + "..." if h and len(h) > 20 else (h or "—"))
        size = details.get("size")
        self._detail_values["Size:"].configure(text=format_file_size(size) if size else "—")

    def _start_dashboard_updater(self):
        self._update_dashboard()
        self.after(1000, self._start_dashboard_updater)

    def _update_dashboard(self):
        if self._current_view != "monitor" or not hasattr(self, '_stat_cards'):
            return
        self._stat_cards["Files Monitored"].configure(text=str(self.monitor.file_count))
        self._stat_cards["Changes Detected"].configure(text=str(self.monitor.total_changes))
        self._stat_cards["Scan Interval"].configure(text=f"{self.monitor.scan_interval}s")
        self._stat_cards["Uptime"].configure(text=self.monitor.uptime_formatted if self.monitor.monitoring else "—")

    def _start_pulse(self):
        if not self.monitor.monitoring:
            return
        self._pulse_state = not self._pulse_state
        color = STATUS_ACTIVE if self._pulse_state else STATUS_PULSE_GLOW
        if hasattr(self, '_status_dot'):
            self._status_dot.configure(text_color=color)
        self.after(800, self._start_pulse)
