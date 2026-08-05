"""把 F:\德國參展\產品照片\尚未轉PNG檔 底下的照片依分類轉成 PNG。

原始檔案完全不動，只在 產品照片\PNG\ 下鏡像同樣的分類結構。
已存在且較新的 PNG 會跳過，可重複執行。
"""
import sys
import json
from pathlib import Path
from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

SRC = Path(r'F:/德國參展/產品照片/尚未轉PNG檔')
DST = Path(r'F:/德國參展/產品照片/PNG')

report = {'converted': [], 'skipped': [], 'failed': []}

folders = sorted(p for p in SRC.iterdir() if p.is_dir())
for folder in folders:
    files = sorted(
        f for f in folder.iterdir()
        if f.is_file() and not f.name.startswith('._')
    )
    out_dir = DST / folder.name
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        out = out_dir / (f.stem + '.png')
        if out.exists() and out.stat().st_mtime >= f.stat().st_mtime:
            report['skipped'].append(str(out.relative_to(DST)))
            continue
        try:
            with Image.open(f) as im:
                im = ImageOps.exif_transpose(im)
                if im.mode not in ('RGB', 'RGBA'):
                    im = im.convert('RGB')
                im.save(out, 'PNG', optimize=True)
            report['converted'].append({
                'src': str(f.relative_to(SRC)),
                'out': str(out.relative_to(DST)),
                'size': im.size,
                'mb': round(out.stat().st_size / 1024 / 1024, 2),
            })
        except Exception as exc:
            report['failed'].append({'src': str(f.relative_to(SRC)), 'error': repr(exc)})
            print(f'FAIL {f.name}: {exc}', file=sys.stderr)

    done = len([r for r in report['converted'] if r['out'].startswith(folder.name)])
    print(f'{folder.name}: {done} converted / {len(files)} files', flush=True)

print()
print(f"converted={len(report['converted'])} skipped={len(report['skipped'])} failed={len(report['failed'])}")
if report['failed']:
    print('FAILED:')
    for r in report['failed']:
        print('  ', r['src'], r['error'])

(Path(__file__).parent / 'heic-to-png-report.json').write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8'
)
