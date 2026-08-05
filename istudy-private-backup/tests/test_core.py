import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from istudy_backup.core import (
    Paths,
    is_target_course,
    normalize_course_name,
    safe_filename,
    stable_video_id,
)


class CoreTests(unittest.TestCase):
    def test_course_range_is_exact(self):
        self.assertTrue(is_target_course(" 115暑電子1 "))
        self.assertTrue(is_target_course("115暑電子15"))
        self.assertFalse(is_target_course("115暑電子0"))
        self.assertFalse(is_target_course("115暑電子16"))
        self.assertFalse(is_target_course("115暑電子1 複習"))

    def test_course_normalization_removes_whitespace_only(self):
        self.assertEqual(normalize_course_name("115 暑 電子 01"), "115暑電子1")

    def test_filename_is_windows_safe(self):
        self.assertEqual(safe_filename('第1講: A/B? <test>.'), "第1講_ A_B_ _test_")
        self.assertEqual(safe_filename("CON"), "_CON")

    def test_stable_id_does_not_change(self):
        first = stable_video_id("115暑電子1", "第一講", "https://example/video/1")
        second = stable_video_id("115暑電子1", "第一講", "https://example/video/1")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)

    def test_paths_create_only_dedicated_runtime_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = Paths.from_root(Path(tmp))
            paths.ensure_runtime_dirs()
            self.assertTrue(paths.profile_dir.is_dir())
            self.assertTrue(paths.downloads_dir.is_dir())
            self.assertTrue(paths.reports_dir.is_dir())
            self.assertTrue(paths.artifacts_dir.is_dir())

    def test_paths_do_not_create_capture_directory(self):
        paths = Paths.from_root(Path("test-root"))
        with patch.object(Path, "mkdir", autospec=True) as mkdir:
            paths.ensure_runtime_dirs()

        created = {call.args[0] for call in mkdir.call_args_list}
        self.assertEqual(
            created,
            {paths.profile_dir, paths.downloads_dir, paths.reports_dir, paths.artifacts_dir},
        )
        self.assertNotIn(paths.capture_file.parent, created)


if __name__ == "__main__":
    unittest.main()
