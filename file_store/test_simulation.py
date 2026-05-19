import unittest
import asyncio
from simulation import FileStore


class TestSimulate(unittest.TestCase):

    # ------------------------------------------------------------------
    # Level 1: upload, get
    # A FileStore stores named files. Uploading the same name overwrites.
    # ------------------------------------------------------------------
    def test_level_1(self):
        fs = FileStore()
        self.assertEqual(fs.upload("readme.txt", "hello"), "uploaded")
        self.assertEqual(fs.upload("notes.txt", "world"), "uploaded")
        self.assertEqual(fs.get("readme.txt"), "hello")
        self.assertEqual(fs.get("notes.txt"), "world")
        self.assertEqual(fs.get("missing.txt"), "file not found")
        # overwrite
        self.assertEqual(fs.upload("readme.txt", "updated"), "uploaded")
        self.assertEqual(fs.get("readme.txt"), "updated")

    # ------------------------------------------------------------------
    # Level 2: copy, search
    # copy(src, dst) duplicates a file's contents under a new name.
    # search(prefix) returns all filenames starting with prefix,
    # sorted alphabetically, comma-separated.
    # ------------------------------------------------------------------
    def test_level_2(self):
        fs = FileStore()
        fs.upload("notes.txt", "abc")
        fs.upload("notes_backup.txt", "bkp")
        fs.upload("report.pdf", "pdf")

        self.assertEqual(fs.copy("notes.txt", "notes_copy.txt"), "copied")
        self.assertEqual(fs.get("notes_copy.txt"), "abc")
        self.assertEqual(fs.copy("ghost.txt", "dest.txt"), "file not found")

        self.assertEqual(fs.search("notes"), "notes.txt,notes_backup.txt,notes_copy.txt")
        self.assertEqual(fs.search("report"), "report.pdf")
        self.assertEqual(fs.search("xyz"), "no files found")

    # ------------------------------------------------------------------
    # Level 3: upload with TTL and timestamp
    # upload(name, content, ttl=None, timestamp=None)
    # get(name, timestamp=None)
    # A file uploaded with ttl expires at upload_timestamp + ttl.
    # get at or after the expiry time returns "file not found".
    # A file uploaded without ttl never expires.
    # get with a timestamp earlier than the upload returns "file not found".
    # ------------------------------------------------------------------
    def test_level_3(self):
        fs = FileStore()

        # expires at 100 + 10 = 110
        fs.upload("temp.txt", "data", ttl=10, timestamp=100)
        self.assertEqual(fs.get("temp.txt", timestamp=105), "data")
        self.assertEqual(fs.get("temp.txt", timestamp=110), "file not found")
        self.assertEqual(fs.get("temp.txt", timestamp=200), "file not found")

        # no ttl = never expires
        fs.upload("perm.txt", "forever", timestamp=50)
        self.assertEqual(fs.get("perm.txt", timestamp=9999), "forever")

        # before upload timestamp
        self.assertEqual(fs.get("perm.txt", timestamp=30), "file not found")

    # ------------------------------------------------------------------
    # Level 4: rollback
    # rollback(timestamp) undoes all uploads that occurred at a timestamp
    # strictly greater than the given value, restoring previous content.
    # ------------------------------------------------------------------
    def test_level_4(self):
        fs = FileStore()

        fs.upload("a.txt", "v1", timestamp=10)
        fs.upload("b.txt", "b_val", timestamp=20)
        fs.upload("a.txt", "v2", timestamp=30)

        self.assertEqual(fs.get("a.txt", timestamp=35), "v2")

        fs.rollback(25)  # undo the t=30 upload of a.txt

        self.assertEqual(fs.get("a.txt", timestamp=35), "v1")   # v2 is gone
        self.assertEqual(fs.get("b.txt", timestamp=35), "b_val") # unaffected
        self.assertEqual(fs.get("a.txt", timestamp=5), "file not found")  # before any upload

    # ------------------------------------------------------------------
    # Level 5: bulk_upload — upload multiple files concurrently
    # Uses threading internally. Returns "uploaded N" where N is the count.
    # ------------------------------------------------------------------
    def test_level_5(self):
        fs = FileStore()
        files = [("a.txt", "aaa"), ("b.txt", "bbb"), ("c.txt", "ccc"), ("d.txt", "ddd")]
        self.assertEqual(fs.bulk_upload(files), "uploaded 4")
        for name, content in files:
            self.assertEqual(fs.get(name), content)

    # ------------------------------------------------------------------
    # Level 6: async_search — search multiple prefixes concurrently
    # Returns a list with one result per prefix, in the same order.
    # Each result is the same as search(prefix) would return.
    # ------------------------------------------------------------------
    def test_level_6(self):
        fs = FileStore()
        fs.upload("x.txt", "xxx")
        fs.upload("x_extra.txt", "extra")
        fs.upload("z.txt", "zzz")

        results = asyncio.run(fs.async_search(["x", "y", "z"]))
        self.assertEqual(results[0], "x.txt,x_extra.txt")
        self.assertEqual(results[1], "no files found")
        self.assertEqual(results[2], "z.txt")


if __name__ == "__main__":
    unittest.main()
