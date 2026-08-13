#!/usr/bin/env python3
"""極簡測試執行器。

本沙箱無法取得 PyPI，因此不依賴 pytest。測試檔本身仍是標準 pytest 格式，
使用者在本機可直接 `pytest tests/` 執行。
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from ahig.bootstrap import configure_stdio  # noqa: E402

configure_stdio()
sys.path.insert(0, str(HERE))


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv):
    targets = ([Path(a) for a in argv] if argv
               else sorted(HERE.glob("test_*.py")))
    total = passed = 0
    failures = []
    for path in targets:
        try:
            mod = load(path)
        except Exception:
            failures.append((path.name, "<import>", traceback.format_exc()))
            print(f"\n{path.name}: IMPORT ERROR")
            continue
        names = [n for n in dir(mod) if n.startswith("test_")]
        print(f"\n{path.name}  ({len(names)} tests)")
        line = []
        for name in names:
            total += 1
            try:
                getattr(mod, name)()
                passed += 1
                line.append(".")
            except Exception:
                line.append("F")
                failures.append((path.name, name, traceback.format_exc()))
        print("  " + "".join(line))

    print("\n" + "=" * 70)
    for fname, tname, tb in failures:
        print(f"\nFAIL {fname}::{tname}")
        print(tb.rstrip())
    print("=" * 70)
    print(f"{passed}/{total} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
