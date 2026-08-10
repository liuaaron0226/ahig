"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  forwardRef,
} from "react";
import {
  motion,
  MotionConfig,
  AnimatePresence,
  type TargetAndTransition,
  type Transition,
} from "motion/react";

type CharAnimDef = {
  initial: TargetAndTransition;
  animate: TargetAndTransition;
  exit: TargetAndTransition;
  transition: Transition;
};
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CursorRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

type CursorState =
  | { type: "hidden" }
  | { type: "caret"; rect: CursorRect }
  | { type: "selection"; rects: CursorRect[] };

/**
 * Character entrance/exit animation preset.
 *
 * - `spring`     — scale + fade with a springy bounce (default)
 * - `bounce`     — exaggerated spring overshoot
 * - `fade`       — simple opacity only
 * - `slide`      — slides up from below
 * - `wave`       — per-char cascading slide (uses CSS delay via index)
 * - `typewriter` — instant appear/disappear, no animation
 */
export type CharAnimation =
  | "spring"
  | "bounce"
  | "fade"
  | "slide"
  | "wave"
  | "typewriter";

/**
 * Visual style of the cursor caret.
 *
 * - `line`       — thin vertical bar (default)
 * - `block`      — full-height filled block behind the char
 * - `underline`  — thin horizontal bar beneath the char
 * - `glow`       — line with a blurred glow halo
 */
export type CursorVariant = "line" | "block" | "underline" | "glow";

/**
 * Pre-built visual preset for the input field itself.
 * Applies a `fieldClassName` baseline that can be overridden.
 *
 * - `default`    — rounded border on dark bg
 * - `ghost`      — no border, subtle bg
 * - `outline`    — border only, transparent bg
 * - `filled`     — solid neutral fill, no border
 * - `terminal`   — monospace, dark green on near-black
 * - `minimal`    — bottom border only (underline style)
 * - `pill`       — heavily rounded, soft bg
 */
export type InputVariant =
  | "default"
  | "ghost"
  | "outline"
  | "filled"
  | "terminal"
  | "minimal"
  | "pill";

// ---------------------------------------------------------------------------
// Preset maps
// ---------------------------------------------------------------------------

const CHAR_ANIMATION_MAP: Record<CharAnimation, CharAnimDef> = {
  spring: {
    initial: { opacity: 0, scale: 0.5, y: 6 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.5, y: -6 },
    transition: { type: "spring", stiffness: 500, damping: 22, mass: 0.4 },
  },
  bounce: {
    initial: { opacity: 0, scale: 0.2, y: 10 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.2, y: -10 },
    transition: { type: "spring", stiffness: 700, damping: 12, mass: 0.3 },
  },
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { type: "tween", duration: 0.15, ease: "easeOut" },
  },
  slide: {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -12 },
    transition: { type: "spring", stiffness: 400, damping: 28 },
  },
  wave: {
    initial: { opacity: 0, y: 8 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 },
    transition: { type: "spring", stiffness: 450, damping: 24 },
  },
  typewriter: {
    initial: { opacity: 1 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0 },
  },
};

const INPUT_VARIANT_CLASSES: Record<InputVariant, string> = {
  default:
    "rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3 text-base text-neutral-100 placeholder:text-neutral-500",
  ghost:
    "rounded-xl bg-neutral-900/40 px-4 py-3 text-base text-neutral-100 placeholder:text-neutral-500",
  outline:
    "rounded-xl border border-neutral-600 bg-transparent px-4 py-3 text-base text-neutral-100 placeholder:text-neutral-500",
  filled:
    "rounded-xl bg-neutral-800 px-4 py-3 text-base text-neutral-100 placeholder:text-neutral-500",
  terminal:
    "rounded-md border border-green-900 bg-neutral-950 px-4 py-3 text-sm font-mono text-green-400 placeholder:text-green-900",
  minimal:
    "border-b border-neutral-700 bg-transparent px-1 py-2 text-base text-neutral-100 placeholder:text-neutral-500 rounded-none",
  pill: "rounded-full border border-neutral-800 bg-neutral-900/60 px-5 py-3 text-base text-neutral-100 placeholder:text-neutral-500",
};

// ---------------------------------------------------------------------------
// Mirror-div cursor measurement
// ---------------------------------------------------------------------------

function measureNativeField(
  field: HTMLInputElement | HTMLTextAreaElement,
  container: HTMLElement,
): CursorState {
  const { selectionStart: ss, selectionEnd: se } = field;
  if (ss === null || se === null) return { type: "hidden" };

  const isTextarea = field.tagName.toLowerCase() === "textarea";
  const fieldRect = field.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  const cs = window.getComputedStyle(field);

  const mirror = document.createElement("div");
  Object.assign(mirror.style, {
    position: "fixed",
    top: `${fieldRect.top}px`,
    left: `${fieldRect.left}px`,
    width: `${fieldRect.width}px`,
    height: `${fieldRect.height}px`,
    visibility: "hidden",
    pointerEvents: "none",
    overflow: "hidden",
    whiteSpace: isTextarea ? "pre-wrap" : "pre",
    wordBreak: isTextarea ? "break-word" : "normal",
    overflowWrap: isTextarea ? "break-word" : "normal",
    boxSizing: cs.boxSizing,
    padding: cs.padding,
    border: cs.border,
    font: cs.font,
    fontSize: cs.fontSize,
    fontFamily: cs.fontFamily,
    fontWeight: cs.fontWeight,
    letterSpacing: cs.letterSpacing,
    lineHeight: cs.lineHeight,
    tabSize: cs.tabSize,
  } as Partial<CSSStyleDeclaration>);

  const value = field.value;
  const before = document.createElement("span");
  before.textContent = value.slice(0, ss);
  const middle = document.createElement("span");
  middle.textContent = ss === se ? "​" : value.slice(ss, se);
  const after = document.createElement("span");
  after.textContent = value.slice(se);

  mirror.appendChild(before);
  mirror.appendChild(middle);
  mirror.appendChild(after);
  document.body.appendChild(mirror);
  mirror.scrollTop = field.scrollTop;
  mirror.scrollLeft = field.scrollLeft;

  const middleRects = Array.from(middle.getClientRects());
  document.body.removeChild(mirror);

  if (middleRects.length === 0) return { type: "hidden" };

  if (ss === se) {
    const r = middleRects[middleRects.length - 1];
    return {
      type: "caret",
      rect: {
        x: r.left - containerRect.left,
        y: r.top - containerRect.top,
        width: 0,
        height: r.height,
      },
    };
  }

  const rects = middleRects
    .filter((r) => r.width > 0)
    .map((r) => ({
      x: r.left - containerRect.left,
      y: r.top - containerRect.top,
      width: r.width,
      height: r.height,
    }));
  return { type: "selection", rects };
}

// ---------------------------------------------------------------------------
// Spring configs
// ---------------------------------------------------------------------------

const CARET_SPRING = {
  type: "spring",
  stiffness: 600,
  damping: 20,
  mass: 0.3,
} as const;

const SELECTION_SPRING = {
  type: "spring",
  stiffness: 600,
  damping: 25,
  mass: 0.3,
} as const;

const MOTION_CONFIG_SPRING = {
  type: "spring",
  stiffness: 600,
  damping: 45,
} as const;

// ---------------------------------------------------------------------------
// CursorOverlay
// ---------------------------------------------------------------------------

const SELECTION_POOL_SIZE = 50;

interface CursorOverlayProps {
  state: CursorState;
  focused: boolean;
  color: string;
  caretWidth: number;
  radius: number;
  variant: CursorVariant;
  blinkSpeed: number;
}

function CursorOverlay({
  state,
  focused,
  color,
  caretWidth,
  radius,
  variant,
  blinkSpeed,
}: CursorOverlayProps) {
  const blinkTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const blinkVisibleRef = useRef(true);
  const caretRef = useRef<HTMLDivElement>(null);

  const isCaret = focused && state.type === "caret";
  const isSelection = focused && state.type === "selection";

  const applyBlink = useCallback(
    (visible: boolean) => {
      blinkVisibleRef.current = visible;
      const node = caretRef.current;
      if (!node) return;
      node.style.opacity = isCaret && visible ? "1" : "0";
    },
    [isCaret],
  );

  useEffect(() => {
    if (blinkTimerRef.current) clearInterval(blinkTimerRef.current);
    blinkTimerRef.current = null;
    applyBlink(true);
    if (isCaret) {
      blinkTimerRef.current = setInterval(
        () => applyBlink(!blinkVisibleRef.current),
        blinkSpeed,
      );
    }
    return () => {
      if (blinkTimerRef.current) clearInterval(blinkTimerRef.current);
    };
  }, [isCaret, applyBlink, blinkSpeed]);

  const caretRect = state.type === "caret" ? state.rect : null;
  const selRects = state.type === "selection" ? state.rects : [];

  const getCaretGeometry = () => {
    if (!caretRect) {
      return {
        x: selRects[0]?.x ?? 0,
        y: selRects[0]?.y ?? 0,
        width: caretWidth,
        height: selRects[0]?.height ?? 0,
      };
    }
    switch (variant) {
      case "block":
        return {
          x: caretRect.x,
          y: caretRect.y,
          width: 9,
          height: caretRect.height,
        };
      case "underline":
        return {
          x: caretRect.x - 2,
          y: caretRect.y + caretRect.height - 2,
          width: 10,
          height: 2,
        };
      default:
        return {
          x: caretRect.x,
          y: caretRect.y,
          width: caretWidth,
          height: caretRect.height,
        };
    }
  };

  const geo = getCaretGeometry();
  const glowStyle =
    variant === "glow" ? { boxShadow: `0 0 6px 2px ${color}` } : {};

  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      <motion.div
        ref={caretRef}
        className="absolute top-0 left-0 origin-left"
        style={{ backgroundColor: color, borderRadius: radius, ...glowStyle }}
        animate={{
          x: geo.x,
          y: geo.y,
          width: geo.width,
          height: geo.height,
          opacity: isCaret ? 1 : 0,
        }}
        transition={CARET_SPRING}
      />
      {Array.from({ length: SELECTION_POOL_SIZE }, (_, i) => {
        const r = selRects[i];
        return (
          <motion.div
            key={i}
            className="absolute top-0 left-0 origin-left"
            style={{ backgroundColor: color, borderRadius: radius }}
            animate={{
              x: r ? r.x : (caretRect?.x ?? 0),
              y: r ? r.y : (caretRect?.y ?? 0),
              width: r ? r.width : 0,
              height: r ? r.height : (caretRect?.height ?? 0),
              opacity: isSelection && r ? 0.28 : 0,
            }}
            transition={SELECTION_SPRING}
          />
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Char — animated character
// ---------------------------------------------------------------------------

interface CharProps {
  id: string;
  char: string;
  anim: CharAnimation;
  index: number;
}

function Char({ id, char, anim, index }: CharProps) {
  const preset = CHAR_ANIMATION_MAP[anim];
  const waveDelay = anim === "wave" ? { delay: index * 0.018 } : {};
  return (
    <motion.span
      key={id}
      layout
      layoutId={id}
      initial={preset.initial}
      animate={preset.animate}
      exit={preset.exit}
      transition={{ ...preset.transition, ...waveDelay }}
      className="inline-block whitespace-pre"
      style={{ transformOrigin: "bottom center" }}
    >
      {char}
    </motion.span>
  );
}

// ---------------------------------------------------------------------------
// Char reconciliation
// ---------------------------------------------------------------------------

interface CharEntry {
  id: string;
  char: string;
}

let _uid = 0;
function uid() {
  return `c${_uid++}`;
}

function reconcileChars(prev: CharEntry[], nextStr: string): CharEntry[] {
  const result: CharEntry[] = [];
  let pi = 0;
  let ni = 0;
  while (ni < nextStr.length) {
    if (pi < prev.length && prev[pi].char === nextStr[ni]) {
      result.push(prev[pi]);
      pi++;
      ni++;
    } else {
      const found = prev.findIndex((c, i) => i > pi && c.char === nextStr[ni]);
      if (found !== -1) {
        pi = found;
      } else {
        result.push({ id: uid(), char: nextStr[ni] });
        ni++;
      }
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Tailwind layout-class extraction
// ---------------------------------------------------------------------------

const LAYOUT_CLASS_PREFIXES = [
  "p-",
  "px-",
  "py-",
  "pt-",
  "pb-",
  "pl-",
  "pr-",
  "text-",
  "font-",
  "leading-",
  "tracking-",
  "tab-",
  "whitespace-",
  "break-",
  "overflow-wrap",
];

function extractLayoutClasses(cls: string): string {
  return cls
    .split(/\s+/)
    .filter((c) => LAYOUT_CLASS_PREFIXES.some((prefix) => c.startsWith(prefix)))
    .join(" ");
}

// ---------------------------------------------------------------------------
// TextCursorTypingInput — public API
// ---------------------------------------------------------------------------

export interface TextCursorTypingInputProps
  extends Omit<
    React.InputHTMLAttributes<HTMLInputElement>,
    "onChange" | "value" | "defaultValue"
  > {
  color?: string;
  caretWidth?: number;
  radius?: number;
  cursorVariant?: CursorVariant;
  blinkSpeed?: number;
  charAnimation?: CharAnimation;
  inputVariant?: InputVariant;
  className?: string;
  fieldClassName?: string;
  multiline?: boolean;
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
}

// Stable instance counter for scoped ::selection suppression.
let _instanceId = 0;

export const TextCursorTypingInput = forwardRef<
  HTMLDivElement,
  TextCursorTypingInputProps
>(function TextCursorTypingInput(
  {
    color = "hsl(220, 100%, 60%)",
    caretWidth = 2,
    radius = 2,
    cursorVariant = "line",
    blinkSpeed = 530,
    charAnimation = "spring",
    inputVariant,
    className,
    fieldClassName = "",
    multiline = false,
    placeholder,
    value: controlledValue,
    defaultValue = "",
    onChange,
    ...nativeProps
  },
  ref,
) {
  const isControlled = controlledValue !== undefined;
  const instanceId = useRef(`tcti-${_instanceId++}`);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const fieldRef = useRef<HTMLInputElement & HTMLTextAreaElement>(null);
  const [cursorState, setCursorState] = useState<CursorState>({
    type: "hidden",
  });
  const [focused, setFocused] = useState(false);
  const [chars, setChars] = useState<CharEntry[]>(() =>
    (isControlled ? controlledValue! : defaultValue)
      .split("")
      .map((c) => ({ id: uid(), char: c })),
  );
  const charsRef = useRef<CharEntry[]>(chars);
  const rafRef = useRef(0);

  useEffect(() => {
    if (!isControlled) return;
    const nextStr = controlledValue!;
    const currentStr = charsRef.current.map((c) => c.char).join("");
    if (nextStr === currentStr) return;
    const next = reconcileChars(charsRef.current, nextStr);
    charsRef.current = next;
    setChars(next);
  }, [isControlled, controlledValue]);

  const measure = useCallback(() => {
    if (!fieldRef.current || !wrapperRef.current) return;
    setCursorState(measureNativeField(fieldRef.current, wrapperRef.current));
  }, []);

  const schedule = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(measure);
  }, [measure]);

  useEffect(() => () => cancelAnimationFrame(rafRef.current), []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const next = reconcileChars(charsRef.current, e.target.value);
      charsRef.current = next;
      setChars(next);
      schedule();
      onChange?.(e.target.value);
    },
    [schedule, onChange],
  );

  const variantBase = inputVariant ? INPUT_VARIANT_CLASSES[inputVariant] : "";
  const resolvedFieldClass = cn(variantBase, fieldClassName);

  const fieldProps = {
    ref: fieldRef,
    ...(isControlled ? { value: controlledValue } : { defaultValue }),
    style: {
      caretColor: "transparent",
      color: "transparent",
      // Suppress native selection highlight — opacity:0 hides the text but
      // ::selection pseudo-element still paints over a transparent color in
      // some browsers, so we also inject a <style> tag (see below).
    } as React.CSSProperties,
    className: cn(
      "absolute inset-0 w-full h-full resize-none bg-transparent outline-none",
      extractLayoutClasses(resolvedFieldClass),
    ),
    onFocus: () => {
      setFocused(true);
      schedule();
    },
    onBlur: () => {
      setFocused(false);
      setCursorState({ type: "hidden" });
    },
    onKeyUp: schedule,
    onMouseUp: schedule,
    onMouseMove: (e: React.MouseEvent) => {
      if (e.buttons === 1) schedule();
    },
    onSelect: schedule,
    onChange: handleChange,
    placeholder: undefined,
    ...nativeProps,
  };

  const setWrapperRef = useCallback(
    (node: HTMLDivElement | null) => {
      (wrapperRef as React.MutableRefObject<HTMLDivElement | null>).current =
        node;
      if (typeof ref === "function") ref(node);
      else if (ref)
        (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
    },
    [ref],
  );

  const id = instanceId.current;

  return (
    <MotionConfig transition={MOTION_CONFIG_SPRING}>
      {/* Suppress native ::selection highlight on the hidden field. */}
      <style>{`[data-tcti="${id}"]::selection,[data-tcti="${id}"]::-moz-selection{background:transparent;color:transparent;}`}</style>
      <div ref={setWrapperRef} className={cn("relative", className)}>
        <div
          aria-hidden
          className={cn(
            "w-full pointer-events-none select-none",
            multiline
              ? "whitespace-pre-wrap wrap-break-word"
              : "whitespace-pre overflow-hidden",
            resolvedFieldClass,
          )}
        >
          {chars.length === 0 && placeholder ? (
            <span className="text-muted-foreground opacity-50">
              {placeholder}
            </span>
          ) : (
            <AnimatePresence initial={false} mode="popLayout">
              {chars.map((entry, i) => (
                <Char
                  key={entry.id}
                  id={entry.id}
                  char={entry.char}
                  anim={charAnimation}
                  index={i}
                />
              ))}
            </AnimatePresence>
          )}
        </div>

        {multiline ? (
          <textarea
            data-tcti={id}
            {...(fieldProps as unknown as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
          />
        ) : (
          <input
            type="text"
            data-tcti={id}
            {...(fieldProps as React.InputHTMLAttributes<HTMLInputElement>)}
          />
        )}

        <CursorOverlay
          state={cursorState}
          focused={focused}
          color={color}
          caretWidth={caretWidth}
          radius={radius}
          variant={cursorVariant}
          blinkSpeed={blinkSpeed}
        />
      </div>
    </MotionConfig>
  );
});

TextCursorTypingInput.displayName = "TextCursorTypingInput";

export default TextCursorTypingInput;
