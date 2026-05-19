import threading
import asyncio
from typing import Optional, List, Tuple


class FileStore:

    def __init__(self):
        self._files = {}
        self._history = []
        self._lock = threading.Lock()

    def upload(self, name: str, content: str,
               ttl: Optional[int] = None,
               timestamp: Optional[int] = None) -> str:
        with self._lock:
            if timestamp is not None:
                self._history.append((timestamp, name, self._files.get(name)))
            self._files[name] = {"content": content, "ttl": ttl, "timestamp": timestamp}
        return "uploaded"

    def get(self, name: str, timestamp: Optional[int] = None) -> str:
        if name not in self._files:
            return "file not found"
        f = self._files[name]
        if timestamp is not None:
            # file didn't exist yet
            if f["timestamp"] is not None and timestamp < f["timestamp"]:
                return "file not found"
            # file has expired
            if f["ttl"] is not None and f["timestamp"] is not None:
                if timestamp >= f["timestamp"] + f["ttl"]:
                    return "file not found"
        return f["content"]

    def copy(self, src: str, dst: str) -> str:
        if src not in self._files:
            return "file not found"
        self.upload(dst, self._files[src]["content"])
        return "copied"

    def search(self, prefix: str) -> str:
        matches = sorted(n for n in self._files if n.startswith(prefix))
        return ",".join(matches) if matches else "no files found"

    def rollback(self, timestamp: int) -> str:
        to_undo = [(ts, n, prev) for ts, n, prev in self._history if ts > timestamp]
        to_undo.sort(key=lambda x: x[0], reverse=True)
        for _, name, prev in to_undo:
            if prev is None:
                self._files.pop(name, None)
            else:
                self._files[name] = prev
        self._history = [(ts, n, p) for ts, n, p in self._history if ts <= timestamp]
        return "rolled back"

    def bulk_upload(self, files: List[Tuple[str, str]]) -> str:
        count = [0]

        def upload_one(name, content):
            self.upload(name, content)
            with self._lock:
                count[0] += 1

        threads = [threading.Thread(target=upload_one, args=(n, c)) for n, c in files]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return f"uploaded {count[0]}"

    async def async_search(self, prefixes: List[str]) -> List[str]:
        async def search_one(prefix):
            return self.search(prefix)
        return list(await asyncio.gather(*[search_one(p) for p in prefixes]))
