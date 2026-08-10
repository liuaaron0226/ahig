export type Direction =
  | "top-bottom"
  | "bottom-top"
  | "left-right"
  | "right-left"
  | "center-out"
  | "center-in";

export type Pattern =
  | "random"
  | "checker"
  | "diagonal"
  | "wave"
  | "spiral"
  | "radial";

export type Easing =
  | "linear"
  | "ease-in"
  | "ease-out"
  | "ease-in-out"
  | "expo-out";

function seededRandom(row: number, col: number, seed: number): number {
  const x = Math.sin(row * 127.1 + col * 311.7 + seed * 113.5) * 43758.5453;
  return x - Math.floor(x);
}

function getDirectionalValue(
  row: number,
  col: number,
  rows: number,
  cols: number,
  direction: Direction,
): number {
  const nr = rows > 1 ? row / (rows - 1) : 0.5;
  const nc = cols > 1 ? col / (cols - 1) : 0.5;

  switch (direction) {
    case "top-bottom":
      return nr;
    case "bottom-top":
      return 1 - nr;
    case "left-right":
      return nc;
    case "right-left":
      return 1 - nc;
    case "center-out": {
      const dx = nr - 0.5;
      const dy = nc - 0.5;
      return Math.min(Math.sqrt(dx * dx + dy * dy) / 0.7071, 1);
    }
    case "center-in": {
      const dx = nr - 0.5;
      const dy = nc - 0.5;
      return 1 - Math.min(Math.sqrt(dx * dx + dy * dy) / 0.7071, 1);
    }
  }
}

function getPatternValue(
  row: number,
  col: number,
  rows: number,
  cols: number,
  pattern: Pattern,
  seed: number,
): number {
  const nr = rows > 1 ? row / (rows - 1) : 0.5;
  const nc = cols > 1 ? col / (cols - 1) : 0.5;

  switch (pattern) {
    case "random":
      return seededRandom(row, col, seed);
    case "checker":
      return (row + col) % 2 === 0 ? 0 : 1;
    case "diagonal": {
      const total = rows + cols - 2;
      return total > 0 ? (row + col) / total : 0.5;
    }
    case "wave":
      return (Math.sin(row * 0.5 + col * 0.3) + 1) / 2;
    case "spiral": {
      const angle = Math.atan2(nr - 0.5, nc - 0.5);
      return (angle + Math.PI) / (2 * Math.PI);
    }
    case "radial": {
      const dx = nr - 0.5;
      const dy = nc - 0.5;
      const dist = Math.sqrt(dx * dx + dy * dy) / 0.7071;
      return Math.floor(dist * 10) / 10;
    }
  }
}

export function computeThresholdMap(
  rows: number,
  cols: number,
  direction: Direction,
  pattern: Pattern,
  patternIntensity: number,
  seed = 42,
): Float32Array {
  const size = rows * cols;
  const map = new Float32Array(size);

  let min = Infinity;
  let max = -Infinity;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const dir = getDirectionalValue(r, c, rows, cols, direction);
      const pat = getPatternValue(r, c, rows, cols, pattern, seed);
      const value = dir * (1 - patternIntensity) + pat * patternIntensity;
      const idx = r * cols + c;

      map[idx] = value;
      if (value < min) min = value;
      if (value > max) max = value;
    }
  }

  const range = max - min || 1;
  for (let i = 0; i < size; i++) {
    map[i] = (map[i] - min) / range;
  }

  return map;
}

export function computeAccentMap(
  rows: number,
  cols: number,
  accentShare: number,
  accentCount: number,
  seed = 42,
): Uint8Array {
  const size = rows * cols;
  const map = new Uint8Array(size);

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const rand = seededRandom(r, c, seed + 999);
      if (rand < accentShare) {
        map[r * cols + c] =
          1 + Math.floor(seededRandom(r, c, seed + 1337) * accentCount);
      }
    }
  }

  return map;
}

export function applyEasing(t: number, easing: Easing): number {
  const clamped = Math.max(0, Math.min(1, t));

  switch (easing) {
    case "linear":
      return clamped;
    case "ease-in":
      return clamped * clamped;
    case "ease-out":
      return 1 - (1 - clamped) * (1 - clamped);
    case "ease-in-out":
      return clamped < 0.5
        ? 2 * clamped * clamped
        : 1 - 2 * (1 - clamped) * (1 - clamped);
    case "expo-out":
      return clamped === 1 ? 1 : 1 - Math.pow(2, -10 * clamped);
  }
}
