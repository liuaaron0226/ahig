# Inventory & Batch Tracking (Module 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the second module of the BixLink inventory system on top of the existing item-master foundation: Partner/Site/Location/Batch/InventoryTransaction schema, a stock-balance query, transaction creation with strict negative-inventory blocking, and CRUD-style API routes — all verified with small synthetic test data, no real Excel data yet.

**Architecture:** Same shape as module 1 — Prisma models, thin service functions that own validation, Next.js route handlers that translate service errors into HTTP status codes. Stock balance is always a computed aggregate over `InventoryTransaction` rows (never a stored running total), so there is exactly one source of truth for "how much stock exists."

**Tech Stack:** Existing project at `C:\Users\User\Desktop\bixlink-wms` — Next.js (App Router) + TypeScript, Vitest, Prisma 6 + SQLite (do not upgrade Prisma — v7's bare `PrismaClient` constructor is broken, confirmed in module 1).

## Global Constraints

- Continue in the existing repo `C:\Users\User\Desktop\bixlink-wms`. Do not touch `project-golem` or anything under `C:\Users\User\Desktop\claude` except this repo's own docs.
- **SQLite has no native `enum` and no scalar list (`String[]`) field type in Prisma.** Every field the spec calls "enum" or an array is a `String` column: enums store the raw string value (e.g. `"PURCHASED"`), validated in the service layer against a `readonly string[]` constant — never with the `in` operator (module 1 shipped a real prototype-chain bypass bug from `in`; use `Array.includes` or `Object.prototype.hasOwnProperty.call`). Arrays store `JSON.stringify(...)`; callers `JSON.parse` on read. This mirrors the existing pattern already in the codebase (`Item.legacyCodes`, `createItem.ts`'s `MAJOR_CATEGORY_LABELS` validation).
- **No PATCH or DELETE routes anywhere in this module.** Per spec §4.3/§4.4: `InventoryTransaction` rows are immutable (corrections are reversing `ADJUST_INCREASE`/`ADJUST_DECREASE` entries, never edits), and master data (`Partner`/`Site`/`Location`/`Item`) uses soft-delete (`isActive`) instead of hard delete. This module adds the `isActive` column and defaults it to `true`; it does **not** add a toggle-`isActive` endpoint — that's future work, not part of this module's approved spec.
- **`BatchAllocation` gets a Prisma model only** — no service function, no API route, in this module. It exists so the schema has the FK relations later modules need; the migration module is what actually populates it.
- **Transfers are not a distinct `type` value.** A site-to-site transfer is two `createTransaction` calls (`OUT` at the source site, `IN` at the destination site) sharing one caller-supplied `transferGroupId` string. There is no `createTransfer` function in this module's approved spec.
- Stock balance formula (spec §4.2): `SUM(IN) + SUM(ADJUST_INCREASE) − SUM(OUT) − SUM(ADJUST_DECREASE)`, filtered to `(itemId, siteId)` and additionally to `batchId` when one is given.
- `OUT` transactions are blocked (400-equivalent thrown error) when `quantity` exceeds the computed balance. `ADJUST_DECREASE` is exempt from this check (spec §4.2).
- Do not re-run `npx prisma migrate dev` interactively in a way that could prompt for destructive reset — if the migration tool proposes a reset, stop and report BLOCKED rather than accepting data loss on `dev.db`.

---

## File Structure

```
bixlink-wms/
  prisma/
    schema.prisma                          (extend — add 6 models + Item.isActive)
    schema.test.ts                         (new — relation/default smoke test)
    migrations/<timestamp>_inventory_batch_tracking/
  src/
    lib/
      partners/
        createPartner.ts
        createPartner.test.ts
      sites/
        createSite.ts
        createSite.test.ts
      locations/
        createLocation.ts
        createLocation.test.ts
      batches/
        createBatch.ts
        createBatch.test.ts
      inventory/
        getStockBalance.ts
        getStockBalance.test.ts
        createTransaction.ts
        createTransaction.test.ts
    app/
      api/
        partners/route.ts, route.test.ts
        sites/route.ts, route.test.ts
        locations/route.ts, route.test.ts
        batches/route.ts, route.test.ts
        transactions/route.ts, route.test.ts
        stock-balance/route.ts, route.test.ts
```

---

## Task 1: Prisma Schema — Partner, Site, Location, Batch, InventoryTransaction, BatchAllocation

**Files:**
- Modify: `prisma/schema.prisma`
- Create: `prisma/schema.test.ts`

**Interfaces:**
- Produces: Prisma Client models `Partner`, `Site`, `Location`, `Batch`, `InventoryTransaction`, `BatchAllocation`; `Item.isActive: boolean` (new column, default `true`).
- Consumed by: every later task in this plan.

- [ ] **Step 1: Write the failing test**

Create `prisma/schema.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../src/lib/db';

describe('module 2 schema', () => {
  beforeEach(async () => {
    await db.batchAllocation.deleteMany();
    await db.inventoryTransaction.deleteMany();
    await db.batch.deleteMany();
    await db.location.deleteMany();
    await db.site.deleteMany();
    await db.partner.deleteMany();
    await db.item.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('creates a Partner, Site, Location, Batch, InventoryTransaction, and BatchAllocation with working relations', async () => {
    const item = await db.item.create({
      data: { itemCode: 'TEST-ITEM-1', categoryKey: 'C_adp', nameSpec: 'test item', unit: 'pcs' },
    });

    const partner = await db.partner.create({
      data: { name: '前瑞', type: JSON.stringify(['代工廠']), isSite: true },
    });

    const site = await db.site.create({
      data: { name: '前瑞工廠', partnerId: partner.id },
    });

    const location = await db.location.create({
      data: { siteId: site.id, code: 'H-15' },
    });

    const batch = await db.batch.create({
      data: { itemId: item.id, batchNo: 'LOT-001', sourceAttribute: 'PURCHASED' },
    });

    const transaction = await db.inventoryTransaction.create({
      data: {
        date: new Date(),
        type: 'IN',
        itemId: item.id,
        batchId: batch.id,
        quantity: 100,
        siteId: site.id,
        locationId: location.id,
      },
    });

    const allocation = await db.batchAllocation.create({
      data: {
        batchId: batch.id,
        finishedItemId: item.id,
        quantity: 10,
        transactionId: transaction.id,
      },
    });

    expect(allocation.id).toBeGreaterThan(0);
    expect(transaction.siteId).toBe(site.id);
  });

  it('defaults isActive to true on Item, Partner, Site, Location', async () => {
    const item = await db.item.create({
      data: { itemCode: 'TEST-ITEM-2', categoryKey: 'C_adp', nameSpec: 'x', unit: 'pcs' },
    });
    const partner = await db.partner.create({ data: { name: 'test-partner', type: '[]' } });
    const site = await db.site.create({ data: { name: 'test-site' } });
    const location = await db.location.create({ data: { siteId: site.id, code: 'A-1' } });

    expect(item.isActive).toBe(true);
    expect(partner.isActive).toBe(true);
    expect(site.isActive).toBe(true);
    expect(location.isActive).toBe(true);
  });

  it('enforces unique (siteId, code) on Location but allows multiple null-code locations per site', async () => {
    const site = await db.site.create({ data: { name: 'unique-test-site' } });
    await db.location.create({ data: { siteId: site.id, code: 'B-1' } });
    await expect(
      db.location.create({ data: { siteId: site.id, code: 'B-1' } })
    ).rejects.toThrow();

    await db.location.create({ data: { siteId: site.id, legacyText: '桌' } });
    await db.location.create({ data: { siteId: site.id, legacyText: '座' } });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- schema.test.ts`
Expected: FAIL — Prisma Client has no `partner`/`site`/`location`/`batch`/`inventoryTransaction`/`batchAllocation` properties (schema doesn't define them yet).

- [ ] **Step 3: Extend the schema**

Replace `prisma/schema.prisma` with:

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
  moq               Int?
  substituteGroupId Int?
  legacyCodes       String?
  isActive          Boolean  @default(true)
  createdAt         DateTime @default(now())

  batches             Batch[]
  finishedAllocations BatchAllocation[]       @relation("BatchAllocationFinishedItem")
  transactions        InventoryTransaction[]
}

model Partner {
  id              Int     @id @default(autoincrement())
  name            String  @unique
  aliases         String?
  type            String
  country         String?
  defaultCurrency String?
  isSite          Boolean @default(false)
  isActive        Boolean @default(true)

  sites          Site[]
  sourcedBatches Batch[]
  transactions   InventoryTransaction[]
}

model Site {
  id        Int      @id @default(autoincrement())
  name      String   @unique
  partnerId Int?
  partner   Partner? @relation(fields: [partnerId], references: [id])
  isActive  Boolean  @default(true)

  locations    Location[]
  transactions InventoryTransaction[]
}

model Location {
  id         Int     @id @default(autoincrement())
  siteId     Int
  site       Site    @relation(fields: [siteId], references: [id])
  code       String?
  legacyText String?
  isActive   Boolean @default(true)

  transactions InventoryTransaction[]

  @@unique([siteId, code])
}

model Batch {
  id              Int       @id @default(autoincrement())
  itemId          Int
  item            Item      @relation(fields: [itemId], references: [id])
  batchNo         String?
  sourcePartnerId Int?
  sourcePartner   Partner?  @relation(fields: [sourcePartnerId], references: [id])
  receivedDate    DateTime?
  sourceAttribute String
  certRefs        String?
  createdAt       DateTime  @default(now())

  transactions InventoryTransaction[]
  allocations  BatchAllocation[]
}

model InventoryTransaction {
  id              Int       @id @default(autoincrement())
  date            DateTime
  type            String
  itemId          Int
  item            Item      @relation(fields: [itemId], references: [id])
  batchId         Int?
  batch           Batch?    @relation(fields: [batchId], references: [id])
  quantity        Int
  siteId          Int
  site            Site      @relation(fields: [siteId], references: [id])
  locationId      Int?
  location        Location? @relation(fields: [locationId], references: [id])
  projectId       String?
  issuedTo        String?
  orderNo         String?
  remark          String?
  partnerId       Int?
  partner         Partner?  @relation(fields: [partnerId], references: [id])
  transferGroupId String?
  createdAt       DateTime  @default(now())

  allocations BatchAllocation[]
}

model BatchAllocation {
  id             Int                   @id @default(autoincrement())
  batchId        Int
  batch          Batch                 @relation(fields: [batchId], references: [id])
  finishedItemId Int
  finishedItem   Item                  @relation("BatchAllocationFinishedItem", fields: [finishedItemId], references: [id])
  quantity       Int
  transactionId  Int?
  transaction    InventoryTransaction? @relation(fields: [transactionId], references: [id])
}
```

- [ ] **Step 4: Run the migration**

```bash
cd C:/Users/User/Desktop/bixlink-wms
npx prisma migrate dev --name inventory_batch_tracking
```

Expected: creates a new migration directory, applies cleanly, reports schema in sync. This is an additive migration (new tables + one new nullable-defaulted column on `Item`) — it must not prompt for data loss. If it does, stop and report BLOCKED with the exact prompt text instead of accepting it.

- [ ] **Step 5: Run the test to verify it passes**

Run: `npm test -- schema.test.ts`
Expected: 3 tests PASS

- [ ] **Step 6: Run the full suite**

Run: `npm test`
Expected: all prior tests (38) plus these 3 pass — 41 total. Confirm `prisma/dev.db` mtime is unchanged by the test run (tests use `prisma/test.db` per `vitest.config.ts`).

- [ ] **Step 7: Commit**

```bash
git add prisma/schema.prisma prisma/schema.test.ts prisma/migrations
git commit -m "feat: add Partner/Site/Location/Batch/InventoryTransaction/BatchAllocation schema"
```

---

## Task 2: Partner Service

**Files:**
- Create: `src/lib/partners/createPartner.ts`
- Test: `src/lib/partners/createPartner.test.ts`

**Interfaces:**
- Produces: `PARTNER_TYPES: readonly string[]`, `createPartner(input: CreatePartnerInput): Promise<Partner>` where
  `CreatePartnerInput = { name: string; aliases?: string[]; type: string[]; country?: string; defaultCurrency?: string; isSite?: boolean }`.
- Consumed by: Task 7 (partners API route).

- [ ] **Step 1: Write the failing tests**

Create `src/lib/partners/createPartner.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { createPartner } from './createPartner';

describe('createPartner', () => {
  beforeEach(async () => {
    await db.partner.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('creates a partner with serialized aliases and type', async () => {
    const partner = await createPartner({
      name: '前瑞',
      aliases: ['Chien Rui'],
      type: ['代工廠', '供應商'],
      country: 'Taiwan',
      defaultCurrency: 'TWD',
      isSite: true,
    });

    expect(partner.name).toBe('前瑞');
    expect(JSON.parse(partner.aliases ?? '[]')).toEqual(['Chien Rui']);
    expect(JSON.parse(partner.type)).toEqual(['代工廠', '供應商']);
    expect(partner.isSite).toBe(true);
  });

  it('rejects an empty type array', async () => {
    await expect(
      createPartner({ name: 'no-type-partner', type: [] })
    ).rejects.toThrow('type must contain at least one value');
  });

  it('rejects an invalid partner type', async () => {
    await expect(
      createPartner({ name: 'bad-type-partner', type: ['經銷商'] })
    ).rejects.toThrow('Invalid partner type "經銷商": must be one of 供應商, 客戶, 代工廠');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- createPartner.test.ts`
Expected: FAIL — `Cannot find module './createPartner'`

- [ ] **Step 3: Implement the service**

Create `src/lib/partners/createPartner.ts`:

```typescript
import { db } from '../db';
import type { Partner } from '@prisma/client';

export const PARTNER_TYPES = ['供應商', '客戶', '代工廠'] as const;

export interface CreatePartnerInput {
  name: string;
  aliases?: string[];
  type: string[];
  country?: string;
  defaultCurrency?: string;
  isSite?: boolean;
}

export async function createPartner(input: CreatePartnerInput): Promise<Partner> {
  if (input.type.length === 0) {
    throw new Error('type must contain at least one value');
  }

  for (const t of input.type) {
    if (!(PARTNER_TYPES as readonly string[]).includes(t)) {
      throw new Error(`Invalid partner type "${t}": must be one of ${PARTNER_TYPES.join(', ')}`);
    }
  }

  return db.partner.create({
    data: {
      name: input.name,
      aliases: input.aliases ? JSON.stringify(input.aliases) : null,
      type: JSON.stringify(input.type),
      country: input.country ?? null,
      defaultCurrency: input.defaultCurrency ?? null,
      isSite: input.isSite ?? false,
    },
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- createPartner.test.ts`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/partners/createPartner.ts src/lib/partners/createPartner.test.ts
git commit -m "feat: add createPartner service with type validation"
```

---

## Task 3: Site & Location Services

**Files:**
- Create: `src/lib/sites/createSite.ts`, `src/lib/sites/createSite.test.ts`
- Create: `src/lib/locations/createLocation.ts`, `src/lib/locations/createLocation.test.ts`

**Interfaces:**
- Produces: `createSite(input: { name: string; partnerId?: number }): Promise<Site>`;
  `createLocation(input: { siteId: number; code?: string; legacyText?: string }): Promise<Location>`.
- Consumed by: Task 7 (sites/locations API routes), Task 6's tests (fixtures).

- [ ] **Step 1: Write the failing tests**

Create `src/lib/sites/createSite.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { createSite } from './createSite';
import { createPartner } from '../partners/createPartner';

describe('createSite', () => {
  beforeEach(async () => {
    await db.site.deleteMany();
    await db.partner.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('creates a site without a partner', async () => {
    const site = await createSite({ name: '得盛倉庫' });
    expect(site.name).toBe('得盛倉庫');
    expect(site.partnerId).toBeNull();
  });

  it('creates a site linked to a partner', async () => {
    const partner = await createPartner({ name: '前瑞', type: ['代工廠'], isSite: true });
    const site = await createSite({ name: '前瑞工廠', partnerId: partner.id });
    expect(site.partnerId).toBe(partner.id);
  });
});
```

Create `src/lib/locations/createLocation.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { createLocation } from './createLocation';
import { createSite } from '../sites/createSite';

describe('createLocation', () => {
  let siteId: number;

  beforeEach(async () => {
    await db.location.deleteMany();
    await db.site.deleteMany();
    const site = await createSite({ name: 'location-test-site' });
    siteId = site.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('creates a location with a code', async () => {
    const location = await createLocation({ siteId, code: 'H-15' });
    expect(location.code).toBe('H-15');
    expect(location.legacyText).toBeNull();
  });

  it('creates a location with only legacyText (no code)', async () => {
    const location = await createLocation({ siteId, legacyText: '防潮箱' });
    expect(location.legacyText).toBe('防潮箱');
    expect(location.code).toBeNull();
  });

  it('rejects a location with neither code nor legacyText', async () => {
    await expect(createLocation({ siteId })).rejects.toThrow(
      'createLocation requires at least one of code or legacyText'
    );
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- createSite.test.ts createLocation.test.ts`
Expected: FAIL — modules not found

- [ ] **Step 3: Implement the services**

Create `src/lib/sites/createSite.ts`:

```typescript
import { db } from '../db';
import type { Site } from '@prisma/client';

export interface CreateSiteInput {
  name: string;
  partnerId?: number;
}

export async function createSite(input: CreateSiteInput): Promise<Site> {
  return db.site.create({
    data: {
      name: input.name,
      partnerId: input.partnerId ?? null,
    },
  });
}
```

Create `src/lib/locations/createLocation.ts`:

```typescript
import { db } from '../db';
import type { Location } from '@prisma/client';

export interface CreateLocationInput {
  siteId: number;
  code?: string;
  legacyText?: string;
}

export async function createLocation(input: CreateLocationInput): Promise<Location> {
  if (!input.code && !input.legacyText) {
    throw new Error('createLocation requires at least one of code or legacyText');
  }

  return db.location.create({
    data: {
      siteId: input.siteId,
      code: input.code ?? null,
      legacyText: input.legacyText ?? null,
    },
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- createSite.test.ts createLocation.test.ts`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/sites/createSite.ts src/lib/sites/createSite.test.ts src/lib/locations/createLocation.ts src/lib/locations/createLocation.test.ts
git commit -m "feat: add createSite and createLocation services"
```

---

## Task 4: Batch Service

**Files:**
- Create: `src/lib/batches/createBatch.ts`
- Test: `src/lib/batches/createBatch.test.ts`

**Interfaces:**
- Produces: `SOURCE_ATTRIBUTES: readonly string[]`, `createBatch(input: CreateBatchInput): Promise<Batch>` where
  `CreateBatchInput = { itemId: number; batchNo?: string; sourcePartnerId?: number; receivedDate?: Date; sourceAttribute: string; certRefs?: string[] }`.
- Consumed by: Task 6 (createTransaction tests use batches as fixtures), Task 7 (batches API route).

- [ ] **Step 1: Write the failing tests**

Create `src/lib/batches/createBatch.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { createBatch } from './createBatch';

describe('createBatch', () => {
  let itemId: number;

  beforeEach(async () => {
    await db.batch.deleteMany();
    await db.item.deleteMany();
    const item = await db.item.create({
      data: { itemCode: 'BATCH-TEST-ITEM', categoryKey: '1電芯', nameSpec: 'test cell', unit: 'pcs' },
    });
    itemId = item.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('creates a batch with a valid sourceAttribute and serialized certRefs', async () => {
    const batch = await createBatch({
      itemId,
      batchNo: 'K312',
      sourceAttribute: 'PURCHASED',
      certRefs: ['UN38.3-2024-001'],
    });

    expect(batch.batchNo).toBe('K312');
    expect(batch.sourceAttribute).toBe('PURCHASED');
    expect(JSON.parse(batch.certRefs ?? '[]')).toEqual(['UN38.3-2024-001']);
  });

  it('rejects an invalid sourceAttribute', async () => {
    await expect(
      createBatch({ itemId, sourceAttribute: 'DONATED' })
    ).rejects.toThrow(
      'Invalid sourceAttribute "DONATED": must be one of PURCHASED, FREE_SAMPLE, CUSTOMER_SUPPLIED'
    );
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- createBatch.test.ts`
Expected: FAIL — `Cannot find module './createBatch'`

- [ ] **Step 3: Implement the service**

Create `src/lib/batches/createBatch.ts`:

```typescript
import { db } from '../db';
import type { Batch } from '@prisma/client';

export const SOURCE_ATTRIBUTES = ['PURCHASED', 'FREE_SAMPLE', 'CUSTOMER_SUPPLIED'] as const;

export interface CreateBatchInput {
  itemId: number;
  batchNo?: string;
  sourcePartnerId?: number;
  receivedDate?: Date;
  sourceAttribute: string;
  certRefs?: string[];
}

export async function createBatch(input: CreateBatchInput): Promise<Batch> {
  if (!(SOURCE_ATTRIBUTES as readonly string[]).includes(input.sourceAttribute)) {
    throw new Error(
      `Invalid sourceAttribute "${input.sourceAttribute}": must be one of ${SOURCE_ATTRIBUTES.join(', ')}`
    );
  }

  return db.batch.create({
    data: {
      itemId: input.itemId,
      batchNo: input.batchNo ?? null,
      sourcePartnerId: input.sourcePartnerId ?? null,
      receivedDate: input.receivedDate ?? null,
      sourceAttribute: input.sourceAttribute,
      certRefs: input.certRefs ? JSON.stringify(input.certRefs) : null,
    },
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- createBatch.test.ts`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/batches/createBatch.ts src/lib/batches/createBatch.test.ts
git commit -m "feat: add createBatch service with source-attribute validation"
```

---

## Task 5: Stock Balance Query

**Files:**
- Create: `src/lib/inventory/getStockBalance.ts`
- Test: `src/lib/inventory/getStockBalance.test.ts`

**Interfaces:**
- Produces: `getStockBalance(query: { itemId: number; siteId: number; batchId?: number }): Promise<number>`.
- Consumed by: Task 6 (`createTransaction`'s negative-stock check), Task 8 (stock-balance API route).

- [ ] **Step 1: Write the failing tests**

Create `src/lib/inventory/getStockBalance.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { getStockBalance } from './getStockBalance';

describe('getStockBalance', () => {
  let itemId: number;
  let siteId: number;
  let otherSiteId: number;
  let batchId: number;
  let otherBatchId: number;

  beforeEach(async () => {
    await db.inventoryTransaction.deleteMany();
    await db.batch.deleteMany();
    await db.site.deleteMany();
    await db.item.deleteMany();

    const item = await db.item.create({
      data: { itemCode: 'BAL-TEST-ITEM', categoryKey: '1電芯', nameSpec: 'x', unit: 'pcs' },
    });
    itemId = item.id;

    const site = await db.site.create({ data: { name: 'bal-site' } });
    siteId = site.id;
    const otherSite = await db.site.create({ data: { name: 'bal-other-site' } });
    otherSiteId = otherSite.id;

    const batch = await db.batch.create({
      data: { itemId, sourceAttribute: 'PURCHASED' },
    });
    batchId = batch.id;
    const otherBatch = await db.batch.create({
      data: { itemId, sourceAttribute: 'PURCHASED' },
    });
    otherBatchId = otherBatch.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('returns 0 when there are no transactions', async () => {
    const balance = await getStockBalance({ itemId, siteId });
    expect(balance).toBe(0);
  });

  it('sums IN and ADJUST_INCREASE, subtracts OUT and ADJUST_DECREASE', async () => {
    await db.inventoryTransaction.createMany({
      data: [
        { date: new Date(), type: 'IN', itemId, siteId, quantity: 100 },
        { date: new Date(), type: 'OUT', itemId, siteId, quantity: 30 },
        { date: new Date(), type: 'ADJUST_INCREASE', itemId, siteId, quantity: 5 },
        { date: new Date(), type: 'ADJUST_DECREASE', itemId, siteId, quantity: 2 },
      ],
    });

    const balance = await getStockBalance({ itemId, siteId });
    expect(balance).toBe(100 - 30 + 5 - 2);
  });

  it('excludes transactions at a different site', async () => {
    await db.inventoryTransaction.createMany({
      data: [
        { date: new Date(), type: 'IN', itemId, siteId, quantity: 50 },
        { date: new Date(), type: 'IN', itemId, siteId: otherSiteId, quantity: 999 },
      ],
    });

    const balance = await getStockBalance({ itemId, siteId });
    expect(balance).toBe(50);
  });

  it('filters to a specific batch when batchId is given', async () => {
    await db.inventoryTransaction.createMany({
      data: [
        { date: new Date(), type: 'IN', itemId, siteId, batchId, quantity: 40 },
        { date: new Date(), type: 'IN', itemId, siteId, batchId: otherBatchId, quantity: 999 },
      ],
    });

    const balance = await getStockBalance({ itemId, siteId, batchId });
    expect(balance).toBe(40);
  });

  it('aggregates across all batches (and non-batch rows) when batchId is omitted', async () => {
    await db.inventoryTransaction.createMany({
      data: [
        { date: new Date(), type: 'IN', itemId, siteId, batchId, quantity: 40 },
        { date: new Date(), type: 'IN', itemId, siteId, batchId: otherBatchId, quantity: 10 },
        { date: new Date(), type: 'IN', itemId, siteId, quantity: 5 },
      ],
    });

    const balance = await getStockBalance({ itemId, siteId });
    expect(balance).toBe(55);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- getStockBalance.test.ts`
Expected: FAIL — `Cannot find module './getStockBalance'`

- [ ] **Step 3: Implement the query**

Create `src/lib/inventory/getStockBalance.ts`:

```typescript
import { db } from '../db';

export interface StockBalanceQuery {
  itemId: number;
  siteId: number;
  batchId?: number;
}

const INCREASING_TYPES = ['IN', 'ADJUST_INCREASE'];
const DECREASING_TYPES = ['OUT', 'ADJUST_DECREASE'];

export async function getStockBalance(query: StockBalanceQuery): Promise<number> {
  const transactions = await db.inventoryTransaction.findMany({
    where: {
      itemId: query.itemId,
      siteId: query.siteId,
      ...(query.batchId !== undefined ? { batchId: query.batchId } : {}),
    },
    select: { type: true, quantity: true },
  });

  return transactions.reduce((balance, t) => {
    if (INCREASING_TYPES.includes(t.type)) return balance + t.quantity;
    if (DECREASING_TYPES.includes(t.type)) return balance - t.quantity;
    return balance;
  }, 0);
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- getStockBalance.test.ts`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/inventory/getStockBalance.ts src/lib/inventory/getStockBalance.test.ts
git commit -m "feat: add getStockBalance aggregate query"
```

---

## Task 6: Transaction Service (with Negative-Inventory Guard)

**Files:**
- Create: `src/lib/inventory/createTransaction.ts`
- Test: `src/lib/inventory/createTransaction.test.ts`

**Interfaces:**
- Consumes: `getStockBalance` from Task 5.
- Produces: `TRANSACTION_TYPES: readonly string[]`, `createTransaction(input: CreateTransactionInput): Promise<InventoryTransaction>` where
  `CreateTransactionInput = { date: Date; type: string; itemId: number; batchId?: number; quantity: number; siteId: number; locationId?: number; projectId?: string; issuedTo?: string; orderNo?: string; remark?: string; partnerId?: number; transferGroupId?: string }`.
- Consumed by: Task 8 (transactions API route).

- [ ] **Step 1: Write the failing tests**

Create `src/lib/inventory/createTransaction.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '../db';
import { createTransaction } from './createTransaction';
import { getStockBalance } from './getStockBalance';

describe('createTransaction', () => {
  let itemId: number;
  let siteId: number;
  let otherSiteId: number;
  let batchId: number;
  let otherBatchId: number;

  beforeEach(async () => {
    await db.inventoryTransaction.deleteMany();
    await db.batch.deleteMany();
    await db.site.deleteMany();
    await db.item.deleteMany();

    const item = await db.item.create({
      data: { itemCode: 'TXN-TEST-ITEM', categoryKey: '1電芯', nameSpec: 'x', unit: 'pcs' },
    });
    itemId = item.id;

    const site = await db.site.create({ data: { name: 'txn-site' } });
    siteId = site.id;
    const otherSite = await db.site.create({ data: { name: 'txn-other-site' } });
    otherSiteId = otherSite.id;

    const batch = await db.batch.create({ data: { itemId, sourceAttribute: 'PURCHASED' } });
    batchId = batch.id;
    const otherBatch = await db.batch.create({ data: { itemId, sourceAttribute: 'PURCHASED' } });
    otherBatchId = otherBatch.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('creates an IN transaction', async () => {
    const txn = await createTransaction({
      date: new Date(),
      type: 'IN',
      itemId,
      siteId,
      quantity: 100,
    });
    expect(txn.type).toBe('IN');
    expect(txn.quantity).toBe(100);
  });

  it('creates an OUT transaction when quantity is within balance', async () => {
    await createTransaction({ date: new Date(), type: 'IN', itemId, siteId, quantity: 100 });
    const out = await createTransaction({ date: new Date(), type: 'OUT', itemId, siteId, quantity: 40 });
    expect(out.quantity).toBe(40);
    expect(await getStockBalance({ itemId, siteId })).toBe(60);
  });

  it('rejects an OUT transaction that exceeds the item+site balance', async () => {
    await createTransaction({ date: new Date(), type: 'IN', itemId, siteId, quantity: 10 });
    await expect(
      createTransaction({ date: new Date(), type: 'OUT', itemId, siteId, quantity: 11 })
    ).rejects.toThrow(
      `Insufficient stock: requested 11, available 10 (itemId=${itemId}, siteId=${siteId})`
    );
  });

  it('rejects an OUT transaction that exceeds the specific batch balance, even if the item+site total would cover it', async () => {
    await createTransaction({ date: new Date(), type: 'IN', itemId, siteId, batchId, quantity: 5 });
    await createTransaction({ date: new Date(), type: 'IN', itemId, siteId, batchId: otherBatchId, quantity: 100 });

    await expect(
      createTransaction({ date: new Date(), type: 'OUT', itemId, siteId, batchId, quantity: 6 })
    ).rejects.toThrow(
      `Insufficient stock: requested 6, available 5 (itemId=${itemId}, siteId=${siteId}, batchId=${batchId})`
    );
  });

  it('allows ADJUST_DECREASE to take the balance below zero', async () => {
    const txn = await createTransaction({
      date: new Date(),
      type: 'ADJUST_DECREASE',
      itemId,
      siteId,
      quantity: 5,
    });
    expect(txn.quantity).toBe(5);
    expect(await getStockBalance({ itemId, siteId })).toBe(-5);
  });

  it('rejects an invalid transaction type', async () => {
    await expect(
      createTransaction({ date: new Date(), type: 'SCRAP', itemId, siteId, quantity: 1 })
    ).rejects.toThrow('Invalid transaction type "SCRAP": must be one of IN, OUT, ADJUST_INCREASE, ADJUST_DECREASE');
  });

  it('represents a site-to-site transfer as two transactions sharing a transferGroupId', async () => {
    await createTransaction({ date: new Date(), type: 'IN', itemId, siteId, quantity: 20 });

    const transferGroupId = 'transfer-1';
    await createTransaction({
      date: new Date(),
      type: 'OUT',
      itemId,
      siteId,
      quantity: 20,
      transferGroupId,
    });
    await createTransaction({
      date: new Date(),
      type: 'IN',
      itemId,
      siteId: otherSiteId,
      quantity: 20,
      transferGroupId,
    });

    expect(await getStockBalance({ itemId, siteId })).toBe(0);
    expect(await getStockBalance({ itemId, siteId: otherSiteId })).toBe(20);

    const pair = await db.inventoryTransaction.findMany({ where: { transferGroupId } });
    expect(pair).toHaveLength(2);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- createTransaction.test.ts`
Expected: FAIL — `Cannot find module './createTransaction'`

- [ ] **Step 3: Implement the service**

Create `src/lib/inventory/createTransaction.ts`:

```typescript
import { db } from '../db';
import { getStockBalance } from './getStockBalance';
import type { InventoryTransaction } from '@prisma/client';

export const TRANSACTION_TYPES = ['IN', 'OUT', 'ADJUST_INCREASE', 'ADJUST_DECREASE'] as const;

export interface CreateTransactionInput {
  date: Date;
  type: string;
  itemId: number;
  batchId?: number;
  quantity: number;
  siteId: number;
  locationId?: number;
  projectId?: string;
  issuedTo?: string;
  orderNo?: string;
  remark?: string;
  partnerId?: number;
  transferGroupId?: string;
}

export async function createTransaction(
  input: CreateTransactionInput
): Promise<InventoryTransaction> {
  if (!(TRANSACTION_TYPES as readonly string[]).includes(input.type)) {
    throw new Error(
      `Invalid transaction type "${input.type}": must be one of ${TRANSACTION_TYPES.join(', ')}`
    );
  }

  if (input.type === 'OUT') {
    const balance = await getStockBalance({
      itemId: input.itemId,
      siteId: input.siteId,
      batchId: input.batchId,
    });
    if (input.quantity > balance) {
      const batchClause = input.batchId !== undefined ? `, batchId=${input.batchId}` : '';
      throw new Error(
        `Insufficient stock: requested ${input.quantity}, available ${balance} (itemId=${input.itemId}, siteId=${input.siteId}${batchClause})`
      );
    }
  }

  return db.inventoryTransaction.create({
    data: {
      date: input.date,
      type: input.type,
      itemId: input.itemId,
      batchId: input.batchId ?? null,
      quantity: input.quantity,
      siteId: input.siteId,
      locationId: input.locationId ?? null,
      projectId: input.projectId ?? null,
      issuedTo: input.issuedTo ?? null,
      orderNo: input.orderNo ?? null,
      remark: input.remark ?? null,
      partnerId: input.partnerId ?? null,
      transferGroupId: input.transferGroupId ?? null,
    },
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- createTransaction.test.ts`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/inventory/createTransaction.ts src/lib/inventory/createTransaction.test.ts
git commit -m "feat: add createTransaction with negative-inventory guard"
```

---

## Task 7: Master-Data API Routes (Partners, Sites, Locations, Batches)

**Files:**
- Create: `src/app/api/partners/route.ts`, `src/app/api/partners/route.test.ts`
- Create: `src/app/api/sites/route.ts`, `src/app/api/sites/route.test.ts`
- Create: `src/app/api/locations/route.ts`, `src/app/api/locations/route.test.ts`
- Create: `src/app/api/batches/route.ts`, `src/app/api/batches/route.test.ts`

**Interfaces:**
- Consumes: `createPartner` (Task 2), `createSite`, `createLocation` (Task 3), `createBatch` (Task 4), `db` (Task 1).
- Produces: `POST`/`GET` for each of `/api/partners`, `/api/sites`, `/api/locations`, `/api/batches` — same 201/400/200 contract as `/api/items` (module 1).

Each route follows the exact pattern established by `src/app/api/items/route.ts`.

- [ ] **Step 1: Write the failing tests**

Create `src/app/api/partners/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { POST, GET } from './route';

describe('/api/partners', () => {
  beforeEach(async () => {
    await db.partner.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('POST creates a partner and returns 201', async () => {
    const request = new Request('http://localhost/api/partners', {
      method: 'POST',
      body: JSON.stringify({ name: '前瑞', type: ['代工廠'], isSite: true }),
    });
    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.name).toBe('前瑞');
  });

  it('POST returns 400 for an invalid type', async () => {
    const request = new Request('http://localhost/api/partners', {
      method: 'POST',
      body: JSON.stringify({ name: 'bad', type: ['經銷商'] }),
    });
    const response = await POST(request);
    expect(response.status).toBe(400);
  });

  it('GET lists partners', async () => {
    await db.partner.create({ data: { name: 'p1', type: '[]' } });
    const response = await GET();
    const body = await response.json();
    expect(body).toHaveLength(1);
  });
});
```

Create `src/app/api/sites/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { POST, GET } from './route';

describe('/api/sites', () => {
  beforeEach(async () => {
    await db.site.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('POST creates a site and returns 201', async () => {
    const request = new Request('http://localhost/api/sites', {
      method: 'POST',
      body: JSON.stringify({ name: '得盛倉庫' }),
    });
    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.name).toBe('得盛倉庫');
  });

  it('GET lists sites', async () => {
    await db.site.create({ data: { name: 's1' } });
    const response = await GET();
    const body = await response.json();
    expect(body).toHaveLength(1);
  });
});
```

Create `src/app/api/locations/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { POST, GET } from './route';

describe('/api/locations', () => {
  let siteId: number;

  beforeEach(async () => {
    await db.location.deleteMany();
    await db.site.deleteMany();
    const site = await db.site.create({ data: { name: 'loc-route-site' } });
    siteId = site.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('POST creates a location and returns 201', async () => {
    const request = new Request('http://localhost/api/locations', {
      method: 'POST',
      body: JSON.stringify({ siteId, code: 'H-15' }),
    });
    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.code).toBe('H-15');
  });

  it('POST returns 400 when neither code nor legacyText is given', async () => {
    const request = new Request('http://localhost/api/locations', {
      method: 'POST',
      body: JSON.stringify({ siteId }),
    });
    const response = await POST(request);
    expect(response.status).toBe(400);
  });

  it('GET lists locations', async () => {
    await db.location.create({ data: { siteId, code: 'A-1' } });
    const response = await GET();
    const body = await response.json();
    expect(body).toHaveLength(1);
  });
});
```

Create `src/app/api/batches/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { POST, GET } from './route';

describe('/api/batches', () => {
  let itemId: number;

  beforeEach(async () => {
    await db.batch.deleteMany();
    await db.item.deleteMany();
    const item = await db.item.create({
      data: { itemCode: 'BATCH-ROUTE-ITEM', categoryKey: '1電芯', nameSpec: 'x', unit: 'pcs' },
    });
    itemId = item.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('POST creates a batch and returns 201', async () => {
    const request = new Request('http://localhost/api/batches', {
      method: 'POST',
      body: JSON.stringify({ itemId, sourceAttribute: 'PURCHASED' }),
    });
    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.sourceAttribute).toBe('PURCHASED');
  });

  it('POST returns 400 for an invalid sourceAttribute', async () => {
    const request = new Request('http://localhost/api/batches', {
      method: 'POST',
      body: JSON.stringify({ itemId, sourceAttribute: 'DONATED' }),
    });
    const response = await POST(request);
    expect(response.status).toBe(400);
  });

  it('GET lists batches', async () => {
    await db.batch.create({ data: { itemId, sourceAttribute: 'PURCHASED' } });
    const response = await GET();
    const body = await response.json();
    expect(body).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- src/app/api/partners src/app/api/sites src/app/api/locations src/app/api/batches`
Expected: FAIL — route modules not found

- [ ] **Step 3: Implement the routes**

Create `src/app/api/partners/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { createPartner } from '@/lib/partners/createPartner';

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const partner = await createPartner({
      name: body.name,
      aliases: body.aliases,
      type: body.type ?? [],
      country: body.country,
      defaultCurrency: body.defaultCurrency,
      isSite: body.isSite,
    });
    return NextResponse.json(partner, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function GET() {
  const partners = await db.partner.findMany({ orderBy: { id: 'desc' } });
  return NextResponse.json(partners);
}
```

Create `src/app/api/sites/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { createSite } from '@/lib/sites/createSite';

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const site = await createSite({ name: body.name, partnerId: body.partnerId });
    return NextResponse.json(site, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function GET() {
  const sites = await db.site.findMany({ orderBy: { id: 'desc' } });
  return NextResponse.json(sites);
}
```

Create `src/app/api/locations/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { createLocation } from '@/lib/locations/createLocation';

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const location = await createLocation({
      siteId: body.siteId,
      code: body.code,
      legacyText: body.legacyText,
    });
    return NextResponse.json(location, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function GET() {
  const locations = await db.location.findMany({ orderBy: { id: 'desc' } });
  return NextResponse.json(locations);
}
```

Create `src/app/api/batches/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { createBatch } from '@/lib/batches/createBatch';

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const batch = await createBatch({
      itemId: body.itemId,
      batchNo: body.batchNo,
      sourcePartnerId: body.sourcePartnerId,
      receivedDate: body.receivedDate ? new Date(body.receivedDate) : undefined,
      sourceAttribute: body.sourceAttribute,
      certRefs: body.certRefs,
    });
    return NextResponse.json(batch, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function GET() {
  const batches = await db.batch.findMany({ orderBy: { createdAt: 'desc' } });
  return NextResponse.json(batches);
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- src/app/api/partners src/app/api/sites src/app/api/locations src/app/api/batches`
Expected: 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/app/api/partners src/app/api/sites src/app/api/locations src/app/api/batches
git commit -m "feat: add /api/partners, /api/sites, /api/locations, /api/batches routes"
```

---

## Task 8: Transaction & Stock-Balance API Routes

**Files:**
- Create: `src/app/api/transactions/route.ts`, `src/app/api/transactions/route.test.ts`
- Create: `src/app/api/stock-balance/route.ts`, `src/app/api/stock-balance/route.test.ts`

**Interfaces:**
- Consumes: `createTransaction` (Task 6), `getStockBalance` (Task 5), `db` (Task 1).
- Produces: `POST`/`GET` `/api/transactions` (201/400/200, same contract as prior routes); `GET /api/stock-balance?itemId=&siteId=&batchId=` → `{ balance: number }`.

- [ ] **Step 1: Write the failing tests**

Create `src/app/api/transactions/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { POST, GET } from './route';

describe('/api/transactions', () => {
  let itemId: number;
  let siteId: number;

  beforeEach(async () => {
    await db.inventoryTransaction.deleteMany();
    await db.site.deleteMany();
    await db.item.deleteMany();
    const item = await db.item.create({
      data: { itemCode: 'TXN-ROUTE-ITEM', categoryKey: '1電芯', nameSpec: 'x', unit: 'pcs' },
    });
    itemId = item.id;
    const site = await db.site.create({ data: { name: 'txn-route-site' } });
    siteId = site.id;
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('POST creates an IN transaction and returns 201', async () => {
    const request = new Request('http://localhost/api/transactions', {
      method: 'POST',
      body: JSON.stringify({ date: new Date().toISOString(), type: 'IN', itemId, siteId, quantity: 50 }),
    });
    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.quantity).toBe(50);
  });

  it('POST returns 400 when an OUT exceeds the balance', async () => {
    const request = new Request('http://localhost/api/transactions', {
      method: 'POST',
      body: JSON.stringify({ date: new Date().toISOString(), type: 'OUT', itemId, siteId, quantity: 5 }),
    });
    const response = await POST(request);
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body.error).toContain('Insufficient stock');
  });

  it('GET lists transactions', async () => {
    await db.inventoryTransaction.create({
      data: { date: new Date(), type: 'IN', itemId, siteId, quantity: 10 },
    });
    const response = await GET();
    const body = await response.json();
    expect(body).toHaveLength(1);
  });
});
```

Create `src/app/api/stock-balance/route.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import { db } from '@/lib/db';
import { GET } from './route';

describe('/api/stock-balance', () => {
  let itemId: number;
  let siteId: number;

  beforeEach(async () => {
    await db.inventoryTransaction.deleteMany();
    await db.site.deleteMany();
    await db.item.deleteMany();
    const item = await db.item.create({
      data: { itemCode: 'BAL-ROUTE-ITEM', categoryKey: '1電芯', nameSpec: 'x', unit: 'pcs' },
    });
    itemId = item.id;
    const site = await db.site.create({ data: { name: 'bal-route-site' } });
    siteId = site.id;
    await db.inventoryTransaction.create({
      data: { date: new Date(), type: 'IN', itemId, siteId, quantity: 42 },
    });
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('GET returns the computed balance for itemId+siteId', async () => {
    const request = new Request(
      `http://localhost/api/stock-balance?itemId=${itemId}&siteId=${siteId}`
    );
    const response = await GET(request);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.balance).toBe(42);
  });

  it('GET returns 400 when itemId or siteId is missing', async () => {
    const request = new Request('http://localhost/api/stock-balance?itemId=' + itemId);
    const response = await GET(request);
    expect(response.status).toBe(400);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- src/app/api/transactions src/app/api/stock-balance`
Expected: FAIL — route modules not found

- [ ] **Step 3: Implement the routes**

Create `src/app/api/transactions/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { createTransaction } from '@/lib/inventory/createTransaction';

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const transaction = await createTransaction({
      date: new Date(body.date),
      type: body.type,
      itemId: body.itemId,
      batchId: body.batchId,
      quantity: body.quantity,
      siteId: body.siteId,
      locationId: body.locationId,
      projectId: body.projectId,
      issuedTo: body.issuedTo,
      orderNo: body.orderNo,
      remark: body.remark,
      partnerId: body.partnerId,
      transferGroupId: body.transferGroupId,
    });
    return NextResponse.json(transaction, { status: 201 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function GET() {
  const transactions = await db.inventoryTransaction.findMany({ orderBy: { createdAt: 'desc' } });
  return NextResponse.json(transactions);
}
```

Create `src/app/api/stock-balance/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { getStockBalance } from '@/lib/inventory/getStockBalance';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const itemIdParam = searchParams.get('itemId');
  const siteIdParam = searchParams.get('siteId');
  const batchIdParam = searchParams.get('batchId');

  if (!itemIdParam || !siteIdParam) {
    return NextResponse.json({ error: 'itemId and siteId are required' }, { status: 400 });
  }

  const balance = await getStockBalance({
    itemId: Number(itemIdParam),
    siteId: Number(siteIdParam),
    batchId: batchIdParam ? Number(batchIdParam) : undefined,
  });

  return NextResponse.json({ balance });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- src/app/api/transactions src/app/api/stock-balance`
Expected: 5 tests PASS

- [ ] **Step 5: Run the full suite**

Run: `npm test`
Expected: all tests pass — 41 (through Task 1) + 3 (Task 2) + 5 (Task 3) + 2 (Task 4) + 5 (Task 5) + 7 (Task 6) + 11 (Task 7) + 5 (Task 8) = 79 total.

- [ ] **Step 6: Commit**

```bash
git add src/app/api/transactions src/app/api/stock-balance
git commit -m "feat: add /api/transactions and /api/stock-balance routes"
```

---

## Plan Self-Review Notes

- **Spec coverage:** Implements spec §3 (Partner/Site/Location/Batch/InventoryTransaction/BatchAllocation schema, including the `Item.isActive` backfill), §4.1 (base-UOM — no conversion logic added, quantities are plain integers), §4.2 (negative-inventory blocking with the exact stated formula and per-batch/per-item granularity), §4.3 (immutability — no update/delete routes anywhere), §4.4 (soft-delete fields present; no deactivation endpoint, matching the spec's actual §5 API list), and §5's named service functions and routes exactly. `BatchAllocation` intentionally gets schema only, per spec §2. TRANSFER is intentionally not a `type` value or a dedicated function, per spec's corrected design.
- **Placeholder scan:** No TBD/TODO. The `in`-operator bypass class of bug from module 1 is explicitly avoided everywhere (Global Constraints calls it out; every validation uses `Array.includes`).
- **Type consistency:** `getStockBalance`'s `StockBalanceQuery` shape is used identically by `createTransaction` (Task 6) and the stock-balance route (Task 8). `createTransaction`'s `CreateTransactionInput` matches exactly what the transactions route (Task 8) passes to it. `createBatch`, `createPartner`, `createSite`, `createLocation` signatures match exactly what their respective routes (Task 7) pass to them.

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-13-inventory-batch-tracking.md`.**
