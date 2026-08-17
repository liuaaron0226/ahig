import io
p = 'COORDINATION.md'
lines = io.open(p, encoding='utf-8').read().split('\n')
out, i = [], 0
n = 0
while i < len(lines):
    if lines[i].startswith('<<<<<<<'):
        b = next(j for j in range(i, len(lines)) if lines[j].startswith('======='))
        c = next(j for j in range(b, len(lines)) if lines[j].startswith('>>>>>>>'))
        ours = lines[i+1:b]
        theirs = lines[b+1:c]
        so = [l for l in ours if l.strip()]
        st = [l for l in theirs if l.strip()]
        # if one side's non-blank content is identical to the other's, keep once
        if so == st:
            keep = ours if len(ours) >= len(theirs) else theirs
            why = 'identical-content'
        elif not so:
            keep = theirs; why = 'ours-blank'
        elif not st:
            keep = ours; why = 'theirs-blank'
        else:
            keep = ours + theirs; why = 'both-kept'
        n += 1
        print('hunk %d @%d: ours=%d theirs=%d -> %s (%d lines)' % (n, i+1, len(so), len(st), why, len(keep)))
        out.extend(keep)
        i = c + 1
    else:
        out.append(lines[i]); i += 1
io.open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('markers left:', sum(1 for l in out if l.startswith(('<<<<<<<', '=======', '>>>>>>>'))))
