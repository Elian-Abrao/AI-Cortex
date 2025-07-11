import pickle
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver


class MemoryManager:
    def __init__(self, base_path: str = "checkpoints"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.saver = InMemorySaver()

    def snapshot_path(self, thread_id: str) -> Path:
        return self.base_path / f"{thread_id}.pkl"

    def save(self, thread_id: str) -> Path:
        path = self.snapshot_path(thread_id)
        state = self.saver.storage.get(thread_id)
        if state is not None:
            with open(path, "wb") as f:
                pickle.dump(state, f)
        return path

    def load(self, thread_id: str) -> None:
        path = self.snapshot_path(thread_id)
        if path.exists():
            with open(path, "rb") as f:
                self.saver.storage[thread_id] = pickle.load(f)