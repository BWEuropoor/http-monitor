import logging
import os
import subprocess
import sys
import time
from threading import Thread
from typing import List, Type

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer


class LogsFileHandler(FileSystemEventHandler):
    def __init__(self, file, controller):
        self.controller = controller
        self.file_path = file
        self.current_length = self.get_file_length()

    def get_file_length(self) -> int:
        """Get file length.

        We're using Unix specific command as reading the length of file will get really
        expensive over time.

        Todo:
            Create platform agnostic equivalent.

        """
        res = subprocess.check_output(["wc", "-l", self.file_path])
        return int(res.strip().split()[0])

    def get_last_n_lines(self, n: int) -> List[str]:
        """Get last n lines of the file.

        Executing `tail` command as it'll be much faster especially when log file grows.

        Todo:
            Create platform agnostic equivalent.

        Args:
            n (int): Number of lines to read.

        Returns
            list: Lines from self.file_path, splitted on new line white character.

        """
        res = str(subprocess.check_output(["tail", f"-n {n}", self.file_path]), "utf-8")
        return res.split("\n")

    def on_modified(self, event: Type[FileModifiedEvent]):
        if not event.is_directory and event.src_path.startswith(self.file_path):
            previous_length, current_length = (
                self.current_length,
                self.get_file_length(),
            )
            n = current_length - previous_length
            if n:
                self.controller.add_lines(self.get_last_n_lines(n))
                self.current_length = current_length


class FileObserver:
    def __init__(self, file_path, controller):
        self.file_path = file_path
        self.controller = controller

        self._watch_thread = Thread(target=self.watch)
        self._watch_thread.daemon = True

    def start(self):
        self._watch_thread.start()

    def watch(self):
        event_handler = LogsFileHandler(self.file_path, self.controller)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(self.file_path), recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            observer.stop()
        observer.join()
