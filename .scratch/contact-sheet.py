"""Build contact sheets so the new folders can be matched to the old reference photos."""
import os, sys, io, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw
import pillow_heif
pillow_heif.register_heif_opener()

SRC = r'F:\德國參展\產品照片'
OLD = r'D:\UserData\Downloads\德國參展\補充照片'
OUT = os.path.dirname(os.path.abspath(__file__))

CELL = 400
COLS = 5


def sheet(items, out_name):
    rows = (len(items) + COLS - 1) // COLS
    canvas = Image.new('RGB', (COLS * CELL, rows * (CELL + 30)), 'white')
    d = ImageDraw.Draw(canvas)
    for i, (label, path) in enumerate(items):
        x = (i % COLS) * CELL
        y = (i // COLS) * (CELL + 30)
        try:
            im = Image.open(path)
            im.thumbnail((CELL - 8, CELL - 8))
            canvas.paste(im, (x + 4, y + 4))
        except Exception as e:
            d.text((x + 8, y + 8), 'ERR %s' % e, fill='red')
        d.text((x + 6, y + CELL + 6), label, fill='black')
    canvas.save(os.path.join(OUT, out_name), quality=88)
    print('wrote', out_name, len(items), 'cells')


# sheet 1: one representative per new folder
new_items = []
for folder in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, folder)
    if not os.path.isdir(p):
        continue
    files = sorted(f for f in os.listdir(p) if not f.startswith('._'))
    if files:
        new_items.append((folder[:22], os.path.join(p, files[0])))
sheet(new_items, 'sheet-new.jpg')

# sheet 2: old approved reference photos
old_items = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(OLD, '*.*')))]
sheet(old_items, 'sheet-old.jpg')
