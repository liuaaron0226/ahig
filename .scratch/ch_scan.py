import json, os, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
print('dirs:', [p.name for p in ROOT.iterdir()])
q=ROOT/'screening-queue'
if q.is_dir():
    print('queue files:', [p.name for p in q.iterdir()][:20])
