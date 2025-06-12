import os
import signal
import sys
import time
import threading
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartOnChange(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print("🔄 Code changed, restarting bot...")
            self.manager.restart_process()

class ProcessManager:
    def __init__(self, script):
        self.script = script
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.stop_process()
        self.process = subprocess.Popen([sys.executable, self.script])

    def stop_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def restart_process(self):
        self.stop_process()
        time.sleep(1)  # ป้องกันการ Restart ถี่เกินไป
        self.start_process()

if __name__ == "__main__":
    manager = ProcessManager("app.py")  # เปลี่ยนจาก main.py เป็น app.py

    event_handler = RestartOnChange(manager)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_process()
        observer.stop()
    observer.join()
