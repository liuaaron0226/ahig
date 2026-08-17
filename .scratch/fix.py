import io
p = 'COORDINATION.md'
lines = io.open(p, encoding='utf-8').read().split('\n')
# 0-indexed positions of the three markers
a = next(i for i, l in enumerate(lines) if l.startswith('<<<<<<<'))
b = next(i for i, l in enumerate(lines) if l.startswith('======='))
c = next(i for i, l in enumerate(lines) if l.startswith('>>>>>>>'))
head = lines[a+1:b]      # coordinator ruling (trunk side)
mine = lines[b+1:c]      # my round-88 heartbeat
# chronological: my round-88 heartbeat was written before the ruling arrived,
# but the ruling commit is earlier on trunk. Keep trunk's ruling first, then mine.
out = lines[:a] + head + mine + lines[c+1:]
io.open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('resolved; markers left:', sum(1 for l in out if l.startswith(('<<<<<<<', '=======', '>>>>>>>'))))
print('ruling lines:', len(head), 'heartbeat lines:', len(mine))
