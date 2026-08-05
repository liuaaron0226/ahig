import os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'F:\德國參展\產品照片'
for folder in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, folder)
    if not os.path.isdir(p):
        continue
    files = sorted(f for f in os.listdir(p) if not f.startswith('._'))
    first = os.path.splitext(files[0])[0] if files else '-'
    last = os.path.splitext(files[-1])[0] if files else '-'
    print('%-34s %3d  %s ~ %s' % (folder, len(files), first, last))
