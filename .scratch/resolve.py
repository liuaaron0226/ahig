import io
p = 'COORDINATION.md'
lines = io.open(p, encoding='utf-8', newline='').read().split('\n')
i_start = next(i for i, l in enumerate(lines) if l.startswith('<<<<<<< HEAD'))
i_mid = next(i for i, l in enumerate(lines) if l.startswith('======='))
i_end = next(i for i, l in enumerate(lines) if l.startswith('>>>>>>> '))
ours = lines[i_start + 1:i_mid]      # page-181 heartbeat
theirs = lines[i_mid + 1:i_end]      # coordinator ruling n+42
# ruling was authored in response to the page-180 heartbeat, so it precedes ours
merged = theirs + [''] + ours
out = lines[:i_start] + merged + lines[i_end + 1:]
io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print('resolved: ruling', len(theirs), 'lines then hb_p181', len(ours), 'lines')
