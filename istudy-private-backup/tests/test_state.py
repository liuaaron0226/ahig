import json
import tempfile
import unittest
from pathlib import Path

from istudy_backup.core import Status, VideoRecord
from istudy_backup.state import StateStore


class StateStoreTests(unittest.TestCase):
    def make_record(self):
        return VideoRecord(
            id="abc123",
            course="115暑電子1",
            title="第一講",
            course_url="https://example/course",
            page_url="https://example/video",
        )

    def test_round_trip_and_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json")
            store.upsert(self.make_record())
            loaded = store.load()
            self.assertEqual(loaded.videos["abc123"].title, "第一講")
            self.assertFalse((Path(tmp) / "state.json.tmp").exists())

    def test_transition_persists_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json")
            store.upsert(self.make_record())
            record = store.transition("abc123", Status.VERIFIED, local_path="x.mp4", method="mp4")
            self.assertEqual(record.status, Status.VERIFIED)
            self.assertEqual(store.load().videos["abc123"].local_path, "x.mp4")

    def test_corrupt_state_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                StateStore(path).load()
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
