# Item Master + 料號編碼引擎 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working subsystem of the BixLink inventory system: a template-driven 料號 (item code) generation engine covering all 16 base material categories, plus the separate 專案代號 (project code) template, backed by a minimal Item Master API and page.

**Architecture:** A pure, framework-free encoding engine (`generateCode(template, inputValues, sequence)`) that composes a fixed-width code string from a list of typed fields (`literal` / `input` / `sequence`). Category-specific business rules live entirely as data (`CodeTemplate` objects), not as branching logic — adding a 17th category later means adding a data entry, not writing new code. This sits behind a thin persistence layer (Prisma + SQLite) and a Next.js API route + page for manual verification.

**Tech Stack:** Next.js (App Router) + TypeScript, Vitest for tests, Prisma ORM + SQLite.

## Global Constraints

- Project root: `C:\Users\User\Desktop\bixlink-wms` (new, independent repo — do not touch `project-golem` or any file under `C:\Users\User\Desktop\claude`).
- Every category template's `generateCode` output must exactly match the real worked example transcribed from `專案命名及編碼原則-20210516R00.xlsx` (see Task 3) — these are the acceptance fixtures, not illustrative examples.
- The leading "大類" (position 1) field of every item-code template is **not** hardcoded as a literal. The source spreadsheet's own reference data is internally inconsistent about what this digit means (a hidden `編碼原則` sheet maps it to a 1–5 "成品/半成品/零件/原物料/外購料" stage, but the observed example values include `6`, which falls outside that range for the `0包材` template). Treat it as a required caller-supplied `input` field in every template until the business confirms the real rule — do not silently invent a validation rule for it.
- Only the 小類 (position 2) field is hardcoded per template, because every one of the 16 worked examples confirms it always equals that category sheet's own leading character.
- `VendorCode` seed data is a **partial, reference-only** lookup (the source only enumerates codes 01–05 and 31–32 for cell vendors; the real transaction log uses values like `15` that aren't in that list). Do not enforce it as a foreign key / hard validation in Phase 1 — store it for future dropdown/autocomplete use only.
- The `Item` model carries three nullable flexibility columns (`moq`, `substituteGroupId`, `legacyCodes`) required by spec §5 for substitute parts, MOQ, and one-material-multiple-codes. This module only defines them in the schema; no task in this plan reads or writes them, and tests must not assert on them. They exist so the future migration module can populate them without a schema change.

---

## File Structure

```
bixlink-wms/
  package.json
  tsconfig.json
  vitest.config.ts
  .env                              (DATABASE_URL, git-ignored)
  prisma/
    schema.prisma
    seed.ts
  src/
    lib/
      coding/
        types.ts                    (TemplateField, CodeTemplate)
        engine.ts                   (generateCode)
        engine.test.ts
        categoryTemplates.ts        (all 16 item-code templates)
        categoryTemplates.test.ts
        projectCodeTemplate.ts      (the separate 專案代號 template)
        projectCodeTemplate.test.ts
      db.ts                         (Prisma client singleton)
      items/
        createItem.ts               (nextSequence lookup + generateCode + persist)
        createItem.test.ts
    app/
      api/
        items/
          route.ts                  (POST create, GET list)
          route.test.ts
      items/
        page.tsx                    (list + create form, manual verification)
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `C:\Users\User\Desktop\bixlink-wms\` (entire Next.js project)
- Create: `C:\Users\User\Desktop\bixlink-wms\vitest.config.ts`
- Create: `C:\Users\User\Desktop\bixlink-wms\src\lib\smoke.test.ts`

**Interfaces:**
- Produces: a working `npm test` command (Vitest) and `npm run dev` (Next.js), which every later task relies on.

- [ ] **Step 1: Scaffold the Next.js app**

Run from `C:\Users\User\Desktop\`:

```bash
npx create-next-app@latest bixlink-wms --typescript --app --no-tailwind --eslint --src-dir --import-alias "@/*" --use-npm --yes
```

- [ ] **Step 2: Install Vitest**

```bash
cd C:/Users/User/Desktop/bixlink-wms
npm install -D vitest
```

- [ ] **Step 3: Add Vitest config**

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
});
```

- [ ] **Step 4: Add the `test` script**

Edit `package.json`, add to `"scripts"`:

```json
"test": "vitest run"
```

- [ ] **Step 5: Write a smoke test**

Create `src/lib/smoke.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';

describe('project scaffold', () => {
  it('runs TypeScript tests via vitest', () => {
    expect(1 + 1).toBe(2);
  });
});
```

- [ ] **Step 6: Run the test to verify the toolchain works**

Run: `npm test`
Expected: 1 test file, 1 test, PASS

- [ ] **Step 7: Init git and commit**

```bash
cd C:/Users/User/Desktop/bixlink-wms
git init
git add -A
git commit -m "chore: scaffold Next.js + TypeScript + Vitest project"
```

---

## Task 2: Coding Engine Core

**Files:**
- Create: `src/lib/coding/types.ts`
- Create: `src/lib/coding/engine.ts`
- Test: `src/lib/coding/engine.test.ts`

**Interfaces:**
- Produces:
  - `TemplateField` type: `{ name: string; kind: 'literal' | 'input' | 'sequence'; length: number; literalValue?: string }`
  - `CodeTemplate` type: `{ key: string; label: string; fields: TemplateField[] }`
  - `generateCode(template: CodeTemplate, inputValues: Record<string, string>, sequenceNumber: number): string`
- Consumed by: Task 3 (`categoryTemplates.ts`), Task 4 (`projectCodeTemplate.ts`), Task 7 (`createItem.ts`).

- [ ] **Step 1: Write the failing tests**

Create `src/lib/coding/types.ts`:

```typescript
export type FieldKind = 'literal' | 'input' | 'sequence';

export interface TemplateField {
  name: string;
  kind: FieldKind;
  length: number;
  /** Required when kind === 'literal'. */
  literalValue?: string;
}

export interface CodeTemplate {
  key: string;
  label: string;
  fields: TemplateField[];
}
```

Create `src/lib/coding/engine.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { generateCode } from './engine';
import type { CodeTemplate } from './types';

const simpleTemplate: CodeTemplate = {
  key: 'test',
  label: 'Test Template',
  fields: [
    { name: 'major', kind: 'literal', length: 1, literalValue: 'X' },
    { name: 'sub', kind: 'input', length: 2 },
    { name: 'seq', kind: 'sequence', length: 3 },
  ],
};

describe('generateCode', () => {
  it('concatenates literal, input, and zero-padded sequence fields in order', () => {
    const code = generateCode(simpleTemplate, { sub: 'AB' }, 7);
    expect(code).toBe('XAB007');
  });

  it('throws when an input field value is missing', () => {
    expect(() => generateCode(simpleTemplate, {}, 1)).toThrow(
      'Missing input value for field "sub"'
    );
  });

  it('throws when an input value does not match the declared field length', () => {
    expect(() => generateCode(simpleTemplate, { sub: 'ABC' }, 1)).toThrow(
      'Field "sub" expected length 2, got "ABC" (length 3)'
    );
  });

  it('throws when the sequence number does not fit in the declared length', () => {
    expect(() => generateCode(simpleTemplate, { sub: 'AB' }, 1000)).toThrow(
      'Sequence number 1000 does not fit in field "seq" (length 3)'
    );
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test`
Expected: FAIL — `Cannot find module './engine'`

- [ ] **Step 3: Implement the engine**

Create `src/lib/coding/engine.ts`:

```typescript
import type { CodeTemplate } from './types';

export function generateCode(
  template: CodeTemplate,
  inputValues: Record<string, string>,
  sequenceNumber: number
): string {
  return template.fields
    .map((field) => {
      if (field.kind === 'literal') {
        return field.literalValue ?? '';
      }

      if (field.kind === 'sequence') {
        const raw = String(sequenceNumber).padStart(field.length, '0');
        if (raw.length > field.length) {
          throw new Error(
            `Sequence number ${sequenceNumber} does not fit in field "${field.name}" (length ${field.length})`
          );
        }
        return raw;
      }

      const value = inputValues[field.name];
      if (value === undefined) {
        throw new Error(`Missing input value for field "${field.name}"`);
      }
      if (value.length !== field.length) {
        throw new Error(
          `Field "${field.name}" expected length ${field.length}, got "${value}" (length ${value.length})`
        );
      }
      return value;
    })
    .join('');
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/coding/types.ts src/lib/coding/engine.ts src/lib/coding/engine.test.ts
git commit -m "feat: add template-driven code generation engine"
```

---

## Task 3: The 16 Item-Code Category Templates

**Files:**
- Create: `src/lib/coding/categoryTemplates.ts`
- Test: `src/lib/coding/categoryTemplates.test.ts`

**Interfaces:**
- Consumes: `CodeTemplate`, `generateCode` from Task 2.
- Produces:
  - `categoryTemplates: CodeTemplate[]` — all 16 templates, keyed by `key`.
  - `getCategoryTemplate(key: string): CodeTemplate` — throws if not found.
- Consumed by: Task 7 (`createItem.ts`).

Each fixture below was hand-decoded from the corresponding sheet in `專案命名及編碼原則-20210516R00.xlsx` and cross-verified to reproduce the sheet's own worked example character-for-character.

- [ ] **Step 1: Write the failing tests**

Create `src/lib/coding/categoryTemplates.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { generateCode } from './engine';
import { categoryTemplates, getCategoryTemplate } from './categoryTemplates';

describe('categoryTemplates', () => {
  it('defines exactly 16 templates', () => {
    expect(categoryTemplates).toHaveLength(16);
  });

  it('throws for an unknown category key', () => {
    expect(() => getCategoryTemplate('nope')).toThrow('Unknown category key: "nope"');
  });

  const cases: Array<{
    key: string;
    inputValues: Record<string, string>;
    sequence: number;
    expected: string;
  }> = [
    {
      key: '1電芯',
      inputValues: { major: '3', seg3: '1', seg4: '2', seg5_6: '15', seg7: '2', seg8: '6' },
      sequence: 1,
      expected: '311215260000001',
    },
    {
      key: '2電子',
      inputValues: {
        major: '5', seg3_4: 'CC', seg5_7: '105', seg8: '4', seg9: '3', seg10: '2', seg11_12: '02',
      },
      sequence: 1,
      expected: '52CC10543202001',
    },
    {
      key: '3塑膠',
      inputValues: { major: '1', seg3_4: '02', seg5_11: 'FN01000', seg12: '1', seg13: '1' },
      sequence: 1,
      expected: '1302FN010001101',
    },
    {
      key: '4標籤',
      inputValues: { major: '3', seg3_4: '01', seg5_11: 'DK01S00', seg12: '2', seg13: '1' },
      sequence: 1,
      expected: '3401DK01S002101',
    },
    {
      key: '5五金',
      inputValues: { major: '3', seg3_4: '05', seg5_11: 'DK01S00', seg12: '2', seg13: '0' },
      sequence: 1,
      expected: '3505DK01S002001',
    },
    {
      key: '6絕緣材',
      inputValues: { major: '3', seg3: '6', seg4_10: 'DK01S00', seg11_12: '10' },
      sequence: 1,
      expected: '366DK01S0010001',
    },
    {
      key: '7連接器',
      inputValues: { major: '3', seg3_4: '03', seg5_9: 'TSN10', seg10_11: '02' },
      sequence: 1,
      expected: '3703TSN10020001',
    },
    {
      key: '8線材',
      inputValues: { major: '3', seg3_4: '01', seg5_11: 'DK01S00', seg12_13: '26' },
      sequence: 1,
      expected: '3801DK01S002601',
    },
    {
      key: '9板子',
      inputValues: { major: '5', seg3_4: '04', seg5_11: 'ZN01000', seg12_13: '03' },
      sequence: 1,
      expected: '5904ZN010000301',
    },
    {
      key: '0包材',
      inputValues: { major: '6', seg3_4: '06', seg5_11: 'DK01S00', seg12: '1' },
      sequence: 1,
      expected: '6006DK01S001001',
    },
    {
      key: 'A電池',
      inputValues: { major: '1', seg3_4: '04', seg5_11: 'RBK01A0', seg12_13: '49' },
      sequence: 1,
      expected: '1A04RBK01A04901',
    },
    {
      key: 'B充電器',
      inputValues: { major: '1', seg3_4: '01', seg5_10: 'FN0100' },
      sequence: 1,
      expected: '1B01FN010000001',
    },
    {
      key: 'C_adp',
      inputValues: { major: '1', seg3_4: '01', seg5_10: 'ATS005', seg11_12: '01' },
      sequence: 1,
      expected: '1C01ATS00501001',
    },
    {
      key: 'D治具',
      inputValues: { major: '1', seg3_4: '03', seg5_11: 'SJ01S00' },
      sequence: 1,
      expected: '1D03SJ01S000001',
    },
    {
      key: 'E面板',
      inputValues: { major: '1', seg3_4: '02', seg5_6: '01', seg7_10: '17R0', seg11_12: '01' },
      sequence: 1,
      expected: '1E020117R001001',
    },
    {
      key: 'F膠類',
      inputValues: { major: '5', seg3_4: '06', seg5_10: 'SX720W' },
      sequence: 1,
      expected: '5F06SX720W00001',
    },
  ];

  it.each(cases)(
    'generates the exact real-world example code for category $key',
    ({ key, inputValues, sequence, expected }) => {
      const template = getCategoryTemplate(key);
      expect(generateCode(template, inputValues, sequence)).toBe(expected);
    }
  );
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test`
Expected: FAIL — `Cannot find module './categoryTemplates'`

- [ ] **Step 3: Implement the 16 templates**

Create `src/lib/coding/categoryTemplates.ts`:

```typescript
import type { CodeTemplate } from './types';

export const categoryTemplates: CodeTemplate[] = [
  {
    key: '1電芯',
    label: '電芯',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '1' },
      { name: 'seg3', kind: 'input', length: 1 },
      { name: 'seg4', kind: 'input', length: 1 },
      { name: 'seg5_6', kind: 'input', length: 2 },
      { name: 'seg7', kind: 'input', length: 1 },
      { name: 'seg8', kind: 'input', length: 1 },
      { name: 'sequence', kind: 'sequence', length: 7 },
    ],
  },
  {
    key: '2電子',
    label: '電子',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '2' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_7', kind: 'input', length: 3 },
      { name: 'seg8', kind: 'input', length: 1 },
      { name: 'seg9', kind: 'input', length: 1 },
      { name: 'seg10', kind: 'input', length: 1 },
      { name: 'seg11_12', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 3 },
    ],
  },
  {
    key: '3塑膠',
    label: '塑膠',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '3' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12', kind: 'input', length: 1 },
      { name: 'seg13', kind: 'input', length: 1 },
      { name: 'sequence', kind: 'sequence', length: 2 },
    ],
  },
  {
    key: '4標籤',
    label: '標籤',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '4' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12', kind: 'input', length: 1 },
      { name: 'seg13', kind: 'input', length: 1 },
      { name: 'sequence', kind: 'sequence', length: 2 },
    ],
  },
  {
    key: '5五金',
    label: '五金',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '5' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12', kind: 'input', length: 1 },
      { name: 'seg13', kind: 'input', length: 1 },
      { name: 'sequence', kind: 'sequence', length: 2 },
    ],
  },
  {
    key: '6絕緣材',
    label: '絕緣材',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '6' },
      { name: 'seg3', kind: 'input', length: 1 },
      { name: 'seg4_10', kind: 'input', length: 7 },
      { name: 'seg11_12', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 3 },
    ],
  },
  {
    key: '7連接器',
    label: '連接器',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '7' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_9', kind: 'input', length: 5 },
      { name: 'seg10_11', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 4 },
    ],
  },
  {
    key: '8線材',
    label: '線材',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '8' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12_13', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 2 },
    ],
  },
  {
    key: '9板子',
    label: '板子',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '9' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12_13', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 2 },
    ],
  },
  {
    key: '0包材',
    label: '包材',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: '0' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12', kind: 'input', length: 1 },
      { name: 'sequence', kind: 'sequence', length: 3 },
    ],
  },
  {
    key: 'A電池',
    label: '電池',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: 'A' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'seg12_13', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 2 },
    ],
  },
  {
    key: 'B充電器',
    label: '充電器',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: 'B' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_10', kind: 'input', length: 6 },
      { name: 'sequence', kind: 'sequence', length: 5 },
    ],
  },
  {
    key: 'C_adp',
    label: 'AC Adapter',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: 'C' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_10', kind: 'input', length: 6 },
      { name: 'seg11_12', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 3 },
    ],
  },
  {
    key: 'D治具',
    label: '治具',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: 'D' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_11', kind: 'input', length: 7 },
      { name: 'sequence', kind: 'sequence', length: 4 },
    ],
  },
  {
    key: 'E面板',
    label: '面板',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: 'E' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_6', kind: 'input', length: 2 },
      { name: 'seg7_10', kind: 'input', length: 4 },
      { name: 'seg11_12', kind: 'input', length: 2 },
      { name: 'sequence', kind: 'sequence', length: 3 },
    ],
  },
  {
    key: 'F膠類',
    label: '膠類',
    fields: [
      { name: 'major', kind: 'input', length: 1 },
      { name: 'minor', kind: 'literal', length: 1, literalValue: 'F' },
      { name: 'seg3_4', kind: 'input', length: 2 },
      { name: 'seg5_10', kind: 'input', length: 6 },
      { name: 'sequence', kind: 'sequence', length: 5 },
    ],
  },
];

export function getCategoryTemplate(key: string): CodeTemplate {
  const template = categoryTemplates.find((t) => t.key === key);
  if (!template) {
    throw new Error(`Unknown category key: "${key}"`);
  }
  return template;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test`
Expected: all tests PASS (2 + 16 parameterized cases)

- [ ] **Step 5: Commit**

```bash
git add src/lib/coding/categoryTemplates.ts src/lib/coding/categoryTemplates.test.ts
git commit -m "feat: define all 16 item-code category templates with real fixtures"
```

---

## Task 4: Project Code Template

**Files:**
- Create: `src/lib/coding/projectCodeTemplate.ts`
- Test: `src/lib/coding/projectCodeTemplate.test.ts`

**Interfaces:**
- Consumes: `CodeTemplate`, `generateCode` from Task 2.
- Produces: `projectCodeTemplate: CodeTemplate`, a 9-character code (大類 + 電芯種類 + 年份 + 串併數[2] + 容量[2] + 流水號[2]).
- Consumed by: Task 7's future project-tracking module (not this plan — Phase 1 Step 3 per the spec's dev order). Included here because it reuses the same engine and the spec groups "編碼引擎" as one deliverable.

The source sheet (`專案命名原則`) labels the last field's position as "14~15", which is inconsistent with the actual 9-character total length of its own worked example — a documentation typo in the source, not a design ambiguity on our end. This plan uses the verified 9-character structure.

- [ ] **Step 1: Write the failing test**

Create `src/lib/coding/projectCodeTemplate.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { generateCode } from './engine';
import { projectCodeTemplate } from './projectCodeTemplate';

describe('projectCodeTemplate', () => {
  it('generates the real worked example project code', () => {
    const code = generateCode(
      projectCodeTemplate,
      {
        productType: 'A',
        chemistry: 'N',
        year: 'A',
        seriesParallel: 'E3',
        capacity: 'A2',
      },
      1
    );
    expect(code).toBe('ANAE3A201');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL — `Cannot find module './projectCodeTemplate'`

- [ ] **Step 3: Implement the template**

Create `src/lib/coding/projectCodeTemplate.ts`:

```typescript
import type { CodeTemplate } from './types';

/**
 * 專案命名原則: productType (A=電池,B=充電器,C=AC Adapter,D=治具,E=面板,F=膠類,G=AD board),
 * chemistry (battery chemistry letter), year (single-char year code), seriesParallel
 * (2-char series+parallel code), capacity (2-char capacity code), sequence (2-digit serial).
 */
export const projectCodeTemplate: CodeTemplate = {
  key: 'project',
  label: '專案代號',
  fields: [
    { name: 'productType', kind: 'input', length: 1 },
    { name: 'chemistry', kind: 'input', length: 1 },
    { name: 'year', kind: 'input', length: 1 },
    { name: 'seriesParallel', kind: 'input', length: 2 },
    { name: 'capacity', kind: 'input', length: 2 },
    { name: 'sequence', kind: 'sequence', length: 2 },
  ],
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/coding/projectCodeTemplate.ts src/lib/coding/projectCodeTemplate.test.ts
git commit -m "feat: add project-code template (separate from item-code templates)"
```

---

## Task 5: Prisma Schema + Migration

**Files:**
- Create: `prisma/schema.prisma`
- Create: `.env` (not committed — see `.gitignore`)
- Create: `src/lib/db.ts`

**Interfaces:**
- Produces: `prisma` Prisma Client models `CategoryLookup`, `VendorCode`, `CustomerRegionCode`, `Item`; and `db` (a `PrismaClient` singleton exported from `src/lib/db.ts`).
- Consumed by: Task 6 (seed), Task 7 (`createItem.ts`), Task 8 (API route).

- [ ] **Step 1: Install Prisma**

```bash
cd C:/Users/User/Desktop/bixlink-wms
npm install prisma --save-dev
npm install @prisma/client
npx prisma init --datasource-provider sqlite
```

- [ ] **Step 2: Write the schema**

Replace the generated `prisma/schema.prisma` with:

```prisma
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model CategoryLookup {
  id              Int    @id @default(autoincrement())
  subcategoryName String @unique
  majorCategory   String
}

model VendorCode {
  id         Int    @id @default(autoincrement())
  code       String
  vendorName String
  scope      String

  @@unique([code, scope])
}

model CustomerRegionCode {
  id         Int    @id @default(autoincrement())
  rangeStart Int
  rangeEnd   Int
  region     String
}

model Item {
  id                Int      @id @default(autoincrement())
  itemCode          String   @unique
  categoryKey       String
  nameSpec          String
  unit              String
  // Flexibility fields per spec §5 — nullable, written by later modules
  // (migration, purchasing), not captured by this module's UI yet:
  moq               Int?     // 最小包裝/訂購數量
  substituteGroupId Int?     // items sharing a group id are substitutes (替代料)
  legacyCodes       String?  // JSON array of historical codes/aliases (一料多號)
  createdAt         DateTime @default(now())
}
```

- [ ] **Step 3: Set the database URL**

Confirm `.env` (created by `prisma init`) contains:

```
DATABASE_URL="file:./dev.db"
```

- [ ] **Step 4: Run the migration**

```bash
npx prisma migrate dev --name init
```

Expected: creates `prisma/dev.db`, prints "Your database is now in sync with your schema."

- [ ] **Step 5: Create the Prisma Client singleton**

Create `src/lib/db.ts`:

```typescript
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

export const db = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = db;
}
```

- [ ] **Step 6: Verify with a throwaway script**

Run:

```bash
node -e "
const { PrismaClient } = require('@prisma/client');
const db = new PrismaClient();
db.item.count().then((n) => { console.log('item count:', n); db.\$disconnect(); });
"
```

Expected: prints `item count: 0` with no errors.

- [ ] **Step 7: Commit**

```bash
git add prisma/schema.prisma src/lib/db.ts .gitignore
git commit -m "feat: add Prisma schema (CategoryLookup, VendorCode, CustomerRegionCode, Item) and migration"
```

Note: confirm `.env` and `prisma/dev.db` are listed in `.gitignore` (Next.js's default `.gitignore` already excludes `.env*`; add `prisma/dev.db` and `prisma/test.db` manually if not already present).

---

## Task 6: Seed Reference Data

**Files:**
- Create: `prisma/seed.ts`
- Test: `prisma/seed.test.ts`

**Interfaces:**
- Consumes: `db` from `src/lib/db.ts`.
- Produces: `seed(): Promise<void>` — idempotent (safe to run multiple times; uses `upsert`).
- Consumed by: manual `npx prisma db seed` runs; not imported by other tasks.

This seeds the full 67-row `類別架構` lookup (transcribed verbatim from the sheet) and the partial, reference-only cell vendor codes and customer region ranges.

- [ ] **Step 1: Write the failing test**

Create `prisma/seed.test.ts`:

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { db } from '../src/lib/db';
import { seed } from './seed';

describe('seed', () => {
  beforeAll(async () => {
    await db.categoryLookup.deleteMany();
    await db.vendorCode.deleteMany();
    await db.customerRegionCode.deleteMany();
    await seed();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('seeds all 67 category lookup rows', async () => {
    const count = await db.categoryLookup.count();
    expect(count).toBe(67);
  });

  it('maps a known subcategory to its major category', async () => {
    const row = await db.categoryLookup.findUnique({ where: { subcategoryName: 'PCB' } });
    expect(row?.majorCategory).toBe('板子');
  });

  it('seeds the known cell vendor codes', async () => {
    const samsung = await db.vendorCode.findFirst({ where: { code: '01', scope: 'cell' } });
    expect(samsung?.vendorName).toBe('三星');
  });

  it('seeds the four customer region ranges', async () => {
    const count = await db.customerRegionCode.count();
    expect(count).toBe(4);
  });

  it('is idempotent: running seed twice does not duplicate rows', async () => {
    await seed();
    const count = await db.categoryLookup.count();
    expect(count).toBe(67);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL — `Cannot find module './seed'`

- [ ] **Step 3: Implement the seed script**

Create `prisma/seed.ts`:

```typescript
import { db } from '../src/lib/db';

const categoryLookup: Array<{ subcategoryName: string; majorCategory: string }> = [
  { subcategoryName: 'ADAPTER', majorCategory: 'ADAPTER' },
  { subcategoryName: 'BOARD', majorCategory: '板子' },
  { subcategoryName: 'CONNECTOR', majorCategory: '連接器' },
  { subcategoryName: 'CR coin', majorCategory: '電池' },
  { subcategoryName: 'DC JACK', majorCategory: '五金' },
  { subcategoryName: 'DIODE', majorCategory: '電子' },
  { subcategoryName: 'EPE', majorCategory: '包材' },
  { subcategoryName: 'FIX NUT', majorCategory: '五金' },
  { subcategoryName: 'FORMEX', majorCategory: '絕緣材' },
  { subcategoryName: 'FUSE', majorCategory: '電子' },
  { subcategoryName: 'Housing', majorCategory: '連接器' },
  { subcategoryName: 'IC', majorCategory: '電子' },
  { subcategoryName: 'LABEL', majorCategory: '標籤' },
  { subcategoryName: 'LED', majorCategory: '電子' },
  { subcategoryName: 'LR coin', majorCategory: '電池' },
  { subcategoryName: 'MALAR', majorCategory: '絕緣材' },
  { subcategoryName: 'MCU', majorCategory: '電子' },
  { subcategoryName: 'MOCKUP', majorCategory: '塑膠' },
  { subcategoryName: 'MODULE', majorCategory: '電池' },
  { subcategoryName: 'MOSFET', majorCategory: '電子' },
  { subcategoryName: 'MS Micro Battery', majorCategory: '電池' },
  { subcategoryName: 'NOMEX', majorCategory: '絕緣材' },
  { subcategoryName: 'NTC', majorCategory: '電子' },
  { subcategoryName: 'ORING', majorCategory: '塑膠' },
  { subcategoryName: 'PANEL', majorCategory: '面板' },
  { subcategoryName: 'PCB', majorCategory: '板子' },
  { subcategoryName: 'PE袋', majorCategory: '包材' },
  { subcategoryName: 'PTC', majorCategory: '電子' },
  { subcategoryName: 'RUBBER', majorCategory: '塑膠' },
  { subcategoryName: 'SCP', majorCategory: '電子' },
  { subcategoryName: 'Shielding', majorCategory: '五金' },
  { subcategoryName: 'SPONGE', majorCategory: '塑膠' },
  { subcategoryName: 'SWITCH', majorCategory: '塑膠' },
  { subcategoryName: 'TERMINAL', majorCategory: '五金' },
  { subcategoryName: 'WAFER', majorCategory: '連接器' },
  { subcategoryName: '二極體', majorCategory: '電子' },
  { subcategoryName: '五金配件', majorCategory: '五金' },
  { subcategoryName: '天地板', majorCategory: '包材' },
  { subcategoryName: '充電器', majorCategory: '充電器' },
  { subcategoryName: '束帶', majorCategory: '塑膠' },
  { subcategoryName: '治具', majorCategory: '治具' },
  { subcategoryName: '長隔板', majorCategory: '包材' },
  { subcategoryName: '保護IC', majorCategory: '電子' },
  { subcategoryName: '恆溫器', majorCategory: '電子' },
  { subcategoryName: '氣泡袋', majorCategory: '包材' },
  { subcategoryName: '紙箱', majorCategory: '包材' },
  { subcategoryName: '液體', majorCategory: '膠類' },
  { subcategoryName: '單面背膠', majorCategory: '標籤' },
  { subcategoryName: '散熱片', majorCategory: '五金' },
  { subcategoryName: '晶體管', majorCategory: '電子' },
  { subcategoryName: '殼蓋', majorCategory: '塑膠' },
  { subcategoryName: '短隔板', majorCategory: '包材' },
  { subcategoryName: '腳墊', majorCategory: '塑膠' },
  { subcategoryName: '電木', majorCategory: '塑膠' },
  { subcategoryName: '電池支架', majorCategory: '塑膠' },
  { subcategoryName: '電容', majorCategory: '電子' },
  { subcategoryName: '電感', majorCategory: '電子' },
  { subcategoryName: '彈片', majorCategory: '五金' },
  { subcategoryName: '線材', majorCategory: '線材' },
  { subcategoryName: '導光柱', majorCategory: '塑膠' },
  { subcategoryName: '導電材料', majorCategory: '五金' },
  { subcategoryName: '螺絲', majorCategory: '五金' },
  { subcategoryName: '黏扣帶', majorCategory: '塑膠' },
  { subcategoryName: '黏著劑', majorCategory: '膠類' },
  { subcategoryName: '鎳片', majorCategory: '五金' },
  { subcategoryName: '護線環', majorCategory: '塑膠' },
];

// Partial, reference-only: source sheet only enumerates 01-05 and 31-32.
// Do not treat as an exhaustive/enforced list (see Global Constraints).
const cellVendorCodes: Array<{ code: string; vendorName: string; scope: string }> = [
  { code: '01', vendorName: '三星', scope: 'cell' },
  { code: '02', vendorName: 'Maxell', scope: 'cell' },
  { code: '03', vendorName: 'LG', scope: 'cell' },
  { code: '04', vendorName: 'PANA(SAYON)', scope: 'cell' },
  { code: '05', vendorName: 'Future Power', scope: 'cell' },
  { code: '31', vendorName: '超創', scope: 'cell' },
  { code: '32', vendorName: 'BixLink品牌', scope: 'cell' },
];

const customerRegionCodes: Array<{ rangeStart: number; rangeEnd: number; region: string }> = [
  { rangeStart: 1, rangeEnd: 2999, region: '日本' },
  { rangeStart: 3001, rangeEnd: 3999, region: '歐美' },
  { rangeStart: 4001, rangeEnd: 4999, region: '台灣' },
  { rangeStart: 5001, rangeEnd: 5999, region: '馬來西亞(其他)' },
];

export async function seed(): Promise<void> {
  for (const row of categoryLookup) {
    await db.categoryLookup.upsert({
      where: { subcategoryName: row.subcategoryName },
      update: { majorCategory: row.majorCategory },
      create: row,
    });
  }

  for (const row of cellVendorCodes) {
    await db.vendorCode.upsert({
      where: { code_scope: { code: row.code, scope: row.scope } },
      update: { vendorName: row.vendorName },
      create: row,
    });
  }

  const existingRegionCount = await db.customerRegionCode.count();
  if (existingRegionCount === 0) {
    await db.customerRegionCode.createMany({ data: customerRegionCodes });
  }
}

if (require.main === module) {
  seed()
    .then(() => db.$disconnect())
    .catch(async (err) => {
      console.error(err);
      await db.$disconnect();
      process.exit(1);
    });
}
```

- [ ] **Step 4: Wire up `prisma db seed`**

Add to `package.json`:

```json
"prisma": {
  "seed": "ts-node prisma/seed.ts"
}
```

```bash
npm install -D ts-node
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npm test`
Expected: 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add prisma/seed.ts prisma/seed.test.ts package.json package-lock.json
git commit -m "feat: seed category lookup, cell vendor codes, and customer region ranges"
```

---

## Task 7: Item Creation Service

**Files:**
- Create: `src/lib/items/createItem.ts`
- Test: `src/lib/items/createItem.test.ts`

**Interfaces:**
- Consumes: `getCategoryTemplate` (Task 3), `generateCode` (Task 2), `db` (Task 5).
- Produces: `createItem(input: CreateItemInput): Promise<Item>` where
  `CreateItemInput = { categoryKey: string; fieldValues: Record<string, string>; nameSpec: string; unit: string }`
  and `Item` is the Prisma `Item` model shape.
- Consumed by: Task 8 (API route).

The per-category sequence number is derived by counting existing `Item` rows with the same `categoryKey` and adding 1.

```
ponytail: sequence = count(existing rows for category) + 1 — a single
read-then-write with no row lock. Fine for one or two concurrent users;
two simultaneous requests for the same category could race and produce
a duplicate sequence. Upgrade to a DB-level counter table with a
transaction/lock if multi-user concurrent item creation becomes real.
```

- [ ] **Step 1: Write the failing tests**

Create `src/lib/items/createItem.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { createItem } from './createItem';

describe('createItem', () => {
  beforeEach(async () => {
    await db.item.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('generates the item code via the category template and persists the item', async () => {
    const item = await createItem({
      categoryKey: 'C_adp',
      fieldValues: { major: '1', seg3_4: '01', seg5_10: 'ATS005', seg11_12: '01' },
      nameSpec: 'AC Adapter (ATS005T-W050U) (日本電容)',
      unit: 'pcs',
    });

    expect(item.itemCode).toBe('1C01ATS00501001');
    expect(item.categoryKey).toBe('C_adp');
    expect(item.nameSpec).toBe('AC Adapter (ATS005T-W050U) (日本電容)');
  });

  it('increments the sequence for the second item in the same category', async () => {
    await createItem({
      categoryKey: 'C_adp',
      fieldValues: { major: '1', seg3_4: '01', seg5_10: 'ATS005', seg11_12: '01' },
      nameSpec: 'First adapter',
      unit: 'pcs',
    });

    const second = await createItem({
      categoryKey: 'C_adp',
      fieldValues: { major: '1', seg3_4: '01', seg5_10: 'ATS005', seg11_12: '01' },
      nameSpec: 'Second adapter',
      unit: 'pcs',
    });

    expect(second.itemCode).toBe('1C01ATS00501002');
  });

  it('throws when the category key is unknown', async () => {
    await expect(
      createItem({ categoryKey: 'nope', fieldValues: {}, nameSpec: 'x', unit: 'pcs' })
    ).rejects.toThrow('Unknown category key: "nope"');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test`
Expected: FAIL — `Cannot find module './createItem'`

- [ ] **Step 3: Implement the service**

Create `src/lib/items/createItem.ts`:

```typescript
import { db } from '../db';
import { generateCode } from '../coding/engine';
import { getCategoryTemplate } from '../coding/categoryTemplates';
import type { Item } from '@prisma/client';

export interface CreateItemInput {
  categoryKey: string;
  fieldValues: Record<string, string>;
  nameSpec: string;
  unit: string;
}

export async function createItem(input: CreateItemInput): Promise<Item> {
  const template = getCategoryTemplate(input.categoryKey);

  const existingCount = await db.item.count({
    where: { categoryKey: input.categoryKey },
  });
  const sequenceNumber = existingCount + 1;

  const itemCode = generateCode(template, input.fieldValues, sequenceNumber);

  return db.item.create({
    data: {
      itemCode,
      categoryKey: input.categoryKey,
      nameSpec: input.nameSpec,
      unit: input.unit,
    },
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/items/createItem.ts src/lib/items/createItem.test.ts
git commit -m "feat: add item creation service with per-category sequence numbering"
```

---

## Task 8: API Route

**Files:**
- Create: `src/app/api/items/route.ts`
- Test: `src/app/api/items/route.test.ts`

**Interfaces:**
- Consumes: `createItem` (Task 7), `db` (Task 5).
- Produces: `POST /api/items` (create, 201 + item JSON, or 400 + `{ error: string }`), `GET /api/items` (200 + `Item[]` JSON, newest first).
- Consumed by: Task 9 (page).

- [ ] **Step 1: Write the failing tests**

Create `src/app/api/items/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { POST, GET } from './route';

describe('/api/items', () => {
  beforeEach(async () => {
    await db.item.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('POST creates an item and returns 201 with the item code', async () => {
    const request = new Request('http://localhost/api/items', {
      method: 'POST',
      body: JSON.stringify({
        categoryKey: 'C_adp',
        fieldValues: { major: '1', seg3_4: '01', seg5_10: 'ATS005', seg11_12: '01' },
        nameSpec: 'AC Adapter (ATS005T-W050U)',
        unit: 'pcs',
      }),
    });

    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.itemCode).toBe('1C01ATS00501001');
  });

  it('POST returns 400 when the category key is unknown', async () => {
    const request = new Request('http://localhost/api/items', {
      method: 'POST',
      body: JSON.stringify({ categoryKey: 'nope', fieldValues: {}, nameSpec: 'x', unit: 'pcs' }),
    });

    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body.error).toBe('Unknown category key: "nope"');
  });

  it('GET lists created items newest first', async () => {
    await db.item.create({
      data: { itemCode: 'AAA', categoryKey: 'C_adp', nameSpec: 'first', unit: 'pcs' },
    });
    await db.item.create({
      data: { itemCode: 'BBB', categoryKey: 'C_adp', nameSpec: 'second', unit: 'pcs' },
    });

    const response = await GET();
    const body = await response.json();

    expect(body).toHaveLength(2);
    expect(body[0].itemCode).toBe('BBB');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test`
Expected: FAIL — `Cannot find module './route'`

- [ ] **Step 3: Implement the route**

Create `src/app/api/items/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { createItem } from '@/lib/items/createItem';

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const item = await createItem({
      categoryKey: body.categoryKey,
      fieldValues: body.fieldValues ?? {},
      nameSpec: body.nameSpec,
      unit: body.unit,
    });
    return NextResponse.json(item, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function GET() {
  const items = await db.item.findMany({ orderBy: { createdAt: 'desc' } });
  return NextResponse.json(items);
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/api/items/route.ts src/app/api/items/route.test.ts
git commit -m "feat: add /api/items POST (create) and GET (list) route"
```

---

## Task 9: Item Master Page (Manual Verification)

**Files:**
- Create: `src/app/items/page.tsx`

**Interfaces:**
- Consumes: `GET /api/items`, `POST /api/items` (Task 8).
- Produces: a browser-viewable page at `/items` listing items and offering a raw-JSON create form. This is the task's manual, human-verified deliverable — no automated test, per the project's UI-verification convention (verify in browser, not just types).

- [ ] **Step 1: Implement the page**

Create `src/app/items/page.tsx`:

```tsx
'use client';

import { useEffect, useState } from 'react';

interface Item {
  id: number;
  itemCode: string;
  categoryKey: string;
  nameSpec: string;
  unit: string;
  createdAt: string;
}

export default function ItemsPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [categoryKey, setCategoryKey] = useState('C_adp');
  const [fieldValuesJson, setFieldValuesJson] = useState(
    '{"major":"1","seg3_4":"01","seg5_10":"ATS005","seg11_12":"01"}'
  );
  const [nameSpec, setNameSpec] = useState('');
  const [unit, setUnit] = useState('pcs');
  const [error, setError] = useState<string | null>(null);

  async function loadItems() {
    const response = await fetch('/api/items');
    setItems(await response.json());
  }

  useEffect(() => {
    loadItems();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    let fieldValues: Record<string, string>;
    try {
      fieldValues = JSON.parse(fieldValuesJson);
    } catch {
      setError('fieldValues must be valid JSON');
      return;
    }

    const response = await fetch('/api/items', {
      method: 'POST',
      body: JSON.stringify({ categoryKey, fieldValues, nameSpec, unit }),
    });
    const body = await response.json();

    if (!response.ok) {
      setError(body.error);
      return;
    }

    setNameSpec('');
    await loadItems();
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>物料主檔 (Item Master)</h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <div>
          <label>
            Category key:{' '}
            <input value={categoryKey} onChange={(e) => setCategoryKey(e.target.value)} />
          </label>
        </div>
        <div>
          <label>
            Field values (JSON):{' '}
            <input
              size={60}
              value={fieldValuesJson}
              onChange={(e) => setFieldValuesJson(e.target.value)}
            />
          </label>
        </div>
        <div>
          <label>
            品名規格:{' '}
            <input value={nameSpec} onChange={(e) => setNameSpec(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            單位: <input value={unit} onChange={(e) => setUnit(e.target.value)} />
          </label>
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">新增料號</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>料號</th>
            <th>類別</th>
            <th>品名規格</th>
            <th>單位</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.itemCode}</td>
              <td>{item.categoryKey}</td>
              <td>{item.nameSpec}</td>
              <td>{item.unit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
```

- [ ] **Step 2: Manually verify in the browser**

```bash
npm run dev
```

Open `http://localhost:3000/items`. Submit the form with the default values pre-filled (category `C_adp`, field values already valid JSON for the AC Adapter template) and a 品名規格 of your choice. Confirm:
- The new row appears in the table with item code `1C01ATS00501001` (or `...002`, `...003` etc. if run more than once).
- Submitting with an invalid `categoryKey` (e.g. `nope`) shows the red error message instead of crashing the page.

- [ ] **Step 3: Commit**

```bash
git add src/app/items/page.tsx
git commit -m "feat: add item master page for manual create/list verification"
```

---

## Plan Self-Review Notes

- **Spec coverage:** This plan implements spec section 6 ("料號 / 專案編碼引擎設計") in full — all 15/16 category templates plus the separate project-code template — and a minimal slice of section 5's `Item` entity and module 1 ("物料主檔與編碼引擎"). `CategoryLookup`, `VendorCode`, and `CustomerRegionCode` reference tables are seeded per spec section 5. Everything else in the spec (Batch, InventoryTransaction, BatchAllocation, Partner, Site, Location, Project, TradeDocument, Reporting, data migration script) is out of scope for this plan — per the spec's own dev-priority order, those come after this module and each deserves its own plan.
- **Placeholder scan:** No TBD/TODO. The one open business ambiguity (大類 digit meaning) is documented as a Global Constraint with the concrete conflicting evidence, and resolved conservatively (treated as required input, not guessed at) rather than left unimplemented.
- **Type consistency:** `CodeTemplate`/`TemplateField` (Task 2) are used identically by `categoryTemplates.ts` (Task 3), `projectCodeTemplate.ts` (Task 4), and `createItem.ts` (Task 7). `createItem`'s `CreateItemInput` shape matches exactly what `route.ts` (Task 8) passes to it, which matches what `page.tsx` (Task 9) sends as the POST body.

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-13-item-master-coding-engine.md`.**
