"""
Simple JSON-file-backed storage for expenses.

Not a database — reads/writes the whole file each call. That's fine at the
scale this assignment targets (a personal expense tracker), and it means
data survives a server restart without needing to stand up a real DB.
"""
import json
import os
import threading


class Storage:
    def __init__(self, filepath="expenses.json"):
        self.filepath = filepath
        self._lock = threading.Lock()
        if not os.path.exists(self.filepath):
            self._write([])

    def _read(self):
        with open(self.filepath, "r") as f:
            return json.load(f)

    def _write(self, data):
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)

    def all(self):
        with self._lock:
            return self._read()

    def add(self, expense: dict):
        with self._lock:
            data = self._read()
            data.append(expense)
            self._write(data)
        return expense

    def get(self, expense_id: str):
        with self._lock:
            data = self._read()
        for e in data:
            if e["id"] == expense_id:
                return e
        return None

    def delete(self, expense_id: str) -> bool:
        with self._lock:
            data = self._read()
            new_data = [e for e in data if e["id"] != expense_id]
            if len(new_data) == len(data):
                return False
            self._write(new_data)
            return True

    def clear(self):
        with self._lock:
            self._write([])
