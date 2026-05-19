import threading
import asyncio
from typing import Optional, List, Tuple


class FileStore:

    def __init__(self):
        self._files = {}    # name -> {content, ttl, timestamp}
        self._history = []  # [(timestamp, name, prev_state), ...]  for rollback
        self._lock = threading.Lock()

    # ---- Level 1 --------------------------------------------------------

    def upload(self, name: str, content: str,
               ttl: Optional[int] = None,
               timestamp: Optional[int] = None) -> str:
        """Store a file. Overwrites if name already exists.
        ttl and timestamp are used from Level 3 onward."""
        # TODO
        pass

    def get(self, name: str, timestamp: Optional[int] = None) -> str:
        """Return file content, or 'file not found'.
        With timestamp: check that the file existed at that time and hasn't expired."""
        # TODO
        pass

    # ---- Level 2 --------------------------------------------------------

    def copy(self, src: str, dst: str) -> str:
        """Copy src to dst. Return 'copied' or 'file not found'."""
        # TODO
        pass

    def search(self, prefix: str) -> str:
        """Return filenames starting with prefix, alphabetical, comma-separated.
        Return 'no files found' if none match."""
        # TODO
        pass

    # ---- Level 4 --------------------------------------------------------

    def rollback(self, timestamp: int) -> str:
        """Undo all uploads with timestamp strictly greater than the given value."""
        # TODO
        pass

    # ---- Level 5 --------------------------------------------------------

    def bulk_upload(self, files: List[Tuple[str, str]]) -> str:
        """Upload each (name, content) pair concurrently using threads.
        Return 'uploaded N' where N is the number of files."""
        # TODO
        pass

    # ---- Level 6 --------------------------------------------------------

    async def async_search(self, prefixes: List[str]) -> List[str]:
        """Search for each prefix concurrently using asyncio.
        Return results in the same order as the input list."""
        # TODO
        pass
