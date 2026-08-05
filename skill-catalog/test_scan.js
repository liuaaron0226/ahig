// Self-check for the skill catalog scanner.
//
//   node test_scan.js

const assert = require('assert');
const { build, classify, parseFrontmatter } = require('./scan.js');

function testFrontmatter() {
  const fm = parseFrontmatter('---\nname: foo\ndescription: "does a thing"\nuser-invocable: true\n---\n# body');
  assert.strictEqual(fm.name, 'foo');
  assert.strictEqual(fm.description, 'does a thing', 'quotes should be stripped');
  assert.strictEqual(parseFrontmatter('# no frontmatter'), null);
  console.log('[frontmatter] OK');
}

function testClassify() {
  // Prefixes are facts and must win over any keyword in the description.
  assert.strictEqual(classify({ name: 'gsd-ship', description: 'design a UI' }), 'dev-flow');
  assert.strictEqual(classify({ name: 'gws-gmail', description: '' }), 'workspace');
  assert.strictEqual(classify({ name: 'persona-researcher', description: '' }), 'persona');

  // Keyword fallback for the 65% of skills with no usable prefix.
  assert.strictEqual(classify({ name: 'frontend-design', description: 'build UI' }), 'design');
  assert.strictEqual(classify({ name: 'cold-email', description: 'outreach campaign' }), 'marketing');

  // Never guess. An unknown skill must surface, not get filed wrongly.
  assert.strictEqual(classify({ name: 'zzz-unknown', description: 'no idea' }), 'uncategorised');
  console.log('[classify] OK');
}

function testBuild() {
  const data = build();

  assert.ok(data.total > 200, `expected a full catalog, got ${data.total}`);
  assert.ok(data.skills.every((s) => s.name), 'every skill needs a name');

  // Names must be unique — duplicates on disk are collapsed, not listed twice.
  const names = data.skills.map((s) => s.name);
  assert.strictEqual(new Set(names).size, names.length, 'names should be deduplicated');

  // The scan cannot see MCP skills; if this drops to zero the merge silently broke.
  assert.ok(data.bySource.mcp > 90, `MCP skills missing (got ${data.bySource.mcp})`);
  assert.ok(data.bySource.local > 100, `local skills missing (got ${data.bySource.local})`);

  // Spot-check both halves of the merge.
  const watchUi = data.skills.find((s) => s.name === 'watch-ui');
  assert.ok(watchUi, 'watch-ui should be found on disk');
  assert.strictEqual(watchUi.source, 'local');
  const gmail = data.skills.find((s) => s.name === 'gws-gmail');
  assert.ok(gmail && gmail.source === 'mcp', 'gws-gmail should come from the MCP list');

  // Descriptions drive search; too many blanks makes search useless.
  const described = data.skills.filter((s) => s.description && s.description.length > 10).length;
  assert.ok(described > data.total * 0.8,
    `only ${described}/${data.total} have usable descriptions — search would be weak`);

  // Classification quality gate: a rule set that files most things as unknown
  // is not doing its job.
  const unc = data.categories.find((c) => c.id === 'uncategorised').count;
  assert.ok(unc < data.total * 0.15,
    `${unc}/${data.total} uncategorised — classification rules need work`);

  // The opposite failure: a broad keyword early in the list swallows the
  // catalog. Workspace legitimately dominates (89 gws-/recipe- skills), so it's
  // exempt; any other single bucket holding a third of everything is a bug.
  for (const c of data.categories) {
    if (c.id === 'workspace' || c.id === 'uncategorised') continue;
    assert.ok(c.count < data.total * 0.33,
      `category "${c.label}" holds ${c.count}/${data.total} — a keyword is too broad`);
  }

  // Marketing skills are a large chunk of this catalog; near-zero means they
  // were absorbed by an earlier rule.
  const marketing = data.categories.find((c) => c.id === 'marketing').count;
  assert.ok(marketing > 20, `only ${marketing} marketing skills — likely miscategorised`);

  console.log(`[build] OK: ${data.total} skills, ${described} described, ${unc} uncategorised`);
  console.log(`         sources: ${JSON.stringify(data.bySource)}`);
  return data;
}

const data = testBuild.length >= 0 ? null : null;
testFrontmatter();
testClassify();
const built = testBuild();
console.log('\n分類分佈:');
for (const c of built.categories) console.log(`  ${String(c.count).padStart(4)}  ${c.label}`);
console.log('\nall checks passed');
