// Build the skill catalog: scan disk, merge the MCP-provided list, classify, emit JSON.
//
//   node scan.js            → writes skills.json next to this file
//   node scan.js --stdout   → prints instead

const fs = require('fs');
const path = require('path');
const os = require('os');
const { MCP_SKILLS } = require('./mcp-skills.js');

const HOME = os.homedir();
const SCAN_ROOTS = [
  { dir: path.join(HOME, '.claude', 'skills'), source: 'local' },
  { dir: path.join(HOME, '.claude', 'plugins', 'cache'), source: 'plugin' },
];

// Ordered: all prefixes are tested first (they're facts), then keywords in this
// order (first match wins). Specific domains must precede generic ones —
// "plan"/"workflow" appear in nearly every marketing skill's description, so a
// broad dev-flow rule placed early swallows most of the catalog.
// Anything matching neither stays uncategorised rather than being forced into a
// bucket — a wrong category is worse than a visible gap (ADR-0005).
const CATEGORIES = [
  { id: 'workspace', label: 'Google Workspace', prefixes: ['gws-', 'recipe-'],
    keywords: ['gmail', 'google calendar', 'google drive', 'google sheet', 'google doc', 'workspace', 'classroom'] },
  { id: 'persona', label: '角色工作流', prefixes: ['persona-'], keywords: [] },
  { id: 'dev-flow', label: '開發流程', prefixes: ['gsd-', 'superpowers'],
    keywords: ['subagent', 'tdd', 'test-driven', 'writing plans', 'executing plans', 'git worktree', 'pull request', 'commit'] },
  { id: 'review', label: '審查與精簡', prefixes: ['ponytail', 'impeccable'],
    keywords: ['code review', 'refactor', 'simplify', 'lint', 'tech debt', 'code quality', 'debug', 'diagnos', 'security review'] },
  { id: 'marketing', label: '行銷與成長', prefixes: [],
    keywords: ['marketing', 'seo', 'ad copy', 'paid advertising', 'campaign', 'growth', 'copywriting', 'cold email', 'pricing', 'competitor', 'customer research', 'churn', 'referral', 'lead magnet', 'social media', 'sales', 'onboarding', 'paywall', 'conversion', 'a/b test', 'experiment', 'aso', 'app store', 'outreach', 'prospect', 'public relations', 'community', 'analytics', 'funnel', 'signup', 'offer'] },
  { id: 'design', label: '設計與前端', prefixes: [],
    keywords: ['design', 'ui', 'ux', 'frontend', 'css', 'theme', 'brand', 'layout', 'typography', 'animation', 'canvas', 'artifact', 'slide', 'banner', 'visual', 'chart', 'dataviz', 'wireframe', 'mockup'] },
  { id: 'media', label: '影音與圖像', prefixes: ['nano-banana'],
    keywords: ['video', 'image gener', 'photo', 'frame', 'transcri', 'audio', 'podcast', 'watch a video', 'screenshot'] },
  { id: 'content', label: '內容生成', prefixes: [],
    keywords: ['write', 'writing', 'content', 'blog', 'article', 'humaniz', 'copy-edit', 'summar', 'research', 'note', 'document', 'presentation'] },
  { id: 'ops', label: '環境與工具', prefixes: ['codex'],
    keywords: ['setup', 'config', 'install', 'permission', 'keybinding', 'hook', 'skill', 'mcp', 'agent', 'loop', 'cron', 'deploy', 'api reference', 'knowledge graph'] },
];

// Minimal YAML-subset reader. Handles the shapes SKILL.md actually uses:
// plain scalars, quoted strings (which routinely contain ": "), block scalars
// (>- and |), and continuation lines. A naive line-by-line regex drops most
// descriptions, and descriptions are what search runs on.
function parseFrontmatter(text) {
  if (!text.startsWith('---')) return null;
  const end = text.indexOf('\n---', 3);
  if (end < 0) return null;

  // Most SKILL.md files on this machine are CRLF; a trailing \r defeats every
  // `$` anchor below and silently yields an empty frontmatter.
  const lines = text.slice(3, end).split('\n').map((l) => l.replace(/\r$/, ''));
  const out = {};
  let key = null;
  let buf = [];
  let blockIndent = null;

  const flush = () => {
    if (!key) return;
    let v = buf.join(' ').trim().replace(/\s+/g, ' ');
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    if (v) out[key] = v;
    key = null;
    buf = [];
    blockIndent = null;
  };

  for (const line of lines) {
    if (!line.trim()) {
      if (blockIndent !== null) buf.push('');
      continue;
    }
    const indent = line.length - line.trimStart().length;

    // Inside a block scalar or a wrapped value: keep consuming indented lines.
    if (key && indent > 0 && (blockIndent !== null || buf.length)) {
      buf.push(line.trim());
      continue;
    }

    const m = line.match(/^([a-zA-Z][\w-]*):(.*)$/);
    if (!m || indent > 0) {
      if (key) buf.push(line.trim());
      continue;
    }

    flush();
    key = m[1];
    const rest = m[2].trim();
    if (rest === '>' || rest === '>-' || rest === '|' || rest === '|-') blockIndent = indent;
    else if (rest) buf.push(rest);
    // Bare `key:` with nested keys under it (e.g. metadata:) — value stays empty.
  }
  flush();
  return out;
}

function classify(skill) {
  const haystack = `${skill.name} ${skill.description || ''}`.toLowerCase();
  for (const cat of CATEGORIES) {
    if (cat.prefixes.some((p) => skill.name.startsWith(p))) return cat.id;
  }
  for (const cat of CATEGORIES) {
    if (cat.keywords.some((k) => haystack.includes(k))) return cat.id;
  }
  return 'uncategorised';
}

function walk(dir, depth, hit) {
  if (depth > 6) return;
  let entries = [];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, depth + 1, hit);
    else if (e.name === 'SKILL.md') hit(p);
  }
}

function scanDisk() {
  const found = new Map(); // name -> skill (first win: local beats plugin)
  for (const { dir, source } of SCAN_ROOTS) {
    if (!fs.existsSync(dir)) continue;
    walk(dir, 0, (file) => {
      let fm;
      try {
        fm = parseFrontmatter(fs.readFileSync(file, 'utf8'));
      } catch {
        return;
      }
      const name = (fm && fm.name) || path.basename(path.dirname(file));
      if (found.has(name)) {
        found.get(name).copies++;
        return;
      }
      found.set(name, {
        name,
        description: (fm && fm.description) || '',
        source,
        copies: 1,
        invocable: !fm || fm['user-invocable'] !== 'false',
        path: file,
      });
    });
  }
  return found;
}

function build() {
  const found = scanDisk();

  // MCP-provided skills never touch disk, so the scan can't see them (ADR-0005).
  for (const s of MCP_SKILLS) {
    if (found.has(s.name)) continue;
    found.set(s.name, {
      name: s.name,
      description: s.description || '',
      source: 'mcp',
      copies: 1,
      invocable: true,
      path: null,
    });
  }

  const skills = [...found.values()]
    .map((s) => ({ ...s, category: classify(s) }))
    .sort((a, b) => a.name.localeCompare(b.name));

  const counts = {};
  for (const s of skills) counts[s.category] = (counts[s.category] || 0) + 1;

  return {
    generatedAt: new Date().toISOString(),
    total: skills.length,
    categories: [
      ...CATEGORIES.map((c) => ({ id: c.id, label: c.label, count: counts[c.id] || 0 })),
      { id: 'uncategorised', label: '未分類', count: counts.uncategorised || 0 },
    ],
    bySource: skills.reduce((a, s) => ((a[s.source] = (a[s.source] || 0) + 1), a), {}),
    skills,
  };
}

module.exports = { build, classify, parseFrontmatter, CATEGORIES };

if (require.main === module) {
  const data = build();
  if (process.argv.includes('--stdout')) {
    console.log(JSON.stringify(data, null, 2));
  } else {
    const out = path.join(__dirname, 'skills.json');
    fs.writeFileSync(out, JSON.stringify(data, null, 2));
    console.log(`${data.total} skills → ${out}`);
    for (const c of data.categories) console.log(`  ${String(c.count).padStart(4)}  ${c.label}`);
    console.log(`  來源:`, JSON.stringify(data.bySource));
  }
}
