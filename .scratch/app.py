import json, os, sys
from pathlib import Path
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.judgement_worksheet import append_judgements
entries = json.load(open(sys.argv[1], encoding='utf-8'))
jb = {"agentClass": "llm", "modelId": "claude-opus-5[1m]",
      "role": "executor-session", "adr": "ADR-0009 ruling-1"}
print(json.dumps(append_judgements(Path(RUN), entries,
      out_name='standard-full-screen-pass-1', judged_by=jb), ensure_ascii=False))
