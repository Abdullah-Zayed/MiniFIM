import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import hashlib
import threading
import time
import os
import json
from datetime import datetime

class MiniFIM:

    def __init__(self, root):

        self.root = root
        self.root.title("Mini File Integrity Monitor")
        self.root.geometry("750x550")

        self.monitoring = False
        self.target_directory = None
        self.baseline = {}
        self.log_file = "fim_alerts.log"
        self.baseline_file = "fim_baseline.json"

        self.setup_ui()


    def setup_ui(self):

        top = tk.Frame(self.root)
        top.pack(pady=10)

        self.select_btn = tk.Button(
            top,
            text="Select Folder",
            command=self.select_directory,
            bg="#0052cc",
            fg="white"
        )
        self.select_btn.grid(row=0, column=0, padx=10)

        self.path_label = tk.Label(top, text="No folder selected", fg="gray")
        self.path_label.grid(row=0, column=1)

        control = tk.Frame(self.root)
        control.pack(pady=10)

        self.status = tk.Label(
            control,
            text="Status: Stopped",
            fg="red",
            font=("Arial", 12, "bold")
        )
        self.status.grid(row=0, column=0, padx=20)

        self.start_btn = tk.Button(
            control,
            text="Start Monitor",
            command=self.start_monitor,
            state=tk.DISABLED,
            bg="green",
            fg="white"
        )
        self.start_btn.grid(row=0, column=1, padx=10)

        self.stop_btn = tk.Button(
            control,
            text="Stop Monitor",
            command=self.stop_monitor,
            state=tk.DISABLED,
            bg="red",
            fg="white"
        )
        self.stop_btn.grid(row=0, column=2, padx=10)

        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(log_frame, text="Integrity Logs").pack(anchor="w")

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas",10),
            state=tk.DISABLED
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.log("FIM initialized. Select a directory to monitor.")


    def log(self,message):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        with open(self.log_file,"a") as f:
            f.write(line)

        self.root.after(0,self._update_log,line)


    def _update_log(self,text):

        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END,text)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)


    def select_directory(self):

        folder = filedialog.askdirectory()

        if folder:

            self.target_directory = folder
            self.path_label.config(text=folder)
            self.start_btn.config(state=tk.NORMAL)

            self.log(f"Monitoring directory selected: {folder}")


    def sha256(self,path):

        hash = hashlib.sha256()

        try:
            with open(path,"rb") as f:
                for block in iter(lambda:f.read(4096),b""):
                    hash.update(block)

            return hash.hexdigest()

        except:
            return None


    def build_baseline(self):

        self.baseline = {}

        for root,dirs,files in os.walk(self.target_directory):

            for name in files:

                path = os.path.join(root,name)

                h = self.sha256(path)

                if h:
                    self.baseline[path] = h

        with open(self.baseline_file,"w") as f:
            json.dump(self.baseline,f,indent=2)

        self.log(f"Baseline created for {len(self.baseline)} files")


    def start_monitor(self):

        if not self.target_directory:
            return

        self.log("Building baseline...")

        self.build_baseline()

        self.monitoring = True

        self.status.config(text="Status: Monitoring", fg="green")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.DISABLED)

        self.thread = threading.Thread(target=self.monitor_loop,daemon=True)
        self.thread.start()


    def stop_monitor(self):

        self.monitoring = False

        self.status.config(text="Status: Stopped", fg="red")

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.NORMAL)

        self.log("Monitoring stopped")


    def monitor_loop(self):

        while self.monitoring:

            time.sleep(3)

            current_files = {}

            for root,dirs,files in os.walk(self.target_directory):

                for name in files:

                    path = os.path.join(root,name)

                    h = self.sha256(path)

                    if h:
                        current_files[path] = h

                        if path not in self.baseline:
                            self.log(f"[ALERT] New file created: {path}")

                        elif self.baseline[path] != h:
                            self.log(f"[ALERT] File modified: {path}")

            for path in self.baseline:

                if path not in current_files:
                    self.log(f"[ALERT] File deleted: {path}")

            self.baseline = current_files


if __name__ == "__main__":

    root = tk.Tk()
    app = MiniFIM(root)
    root.mainloop()