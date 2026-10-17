"use client";

import { useSyncExternalStore } from "react";
import { flushSync } from "react-dom";
import { THEME_STORAGE_KEY } from "@/lib/theme-script";

export type Theme = "light" | "dark";

/** Viewport coordinates the theme change should grow from (usually the toggle button). */
export interface TransitionOrigin {
  x: number;
  y: number;
}

const CHANGE_EVENT = "sarpebe-themechange";
const REVEAL_DURATION_MS = 550;
const REVEAL_EASING = "cubic-bezier(0.65, 0, 0.35, 1)";

function readTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => window.removeEventListener(CHANGE_EVENT, onChange);
}

function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Private mode or blocked storage: the choice just won't persist.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

/**
 * Switches the theme. With an origin, the new theme is revealed through a circle that grows
 * from that point (View Transitions API + clip-path). The change is instant when the browser
 * lacks the API, when no origin is given, or when the user prefers reduced motion.
 */
export function setTheme(theme: Theme, origin?: TransitionOrigin): void {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!origin || reduceMotion || typeof document.startViewTransition !== "function") {
    applyTheme(theme);
    return;
  }

  const { x, y } = origin;
  // Radius to the farthest corner, so the circle always ends up covering the whole viewport.
  const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));

  // flushSync makes React render the new theme before the browser captures the "after" frame.
  const transition = document.startViewTransition(() => {
    flushSync(() => applyTheme(theme));
  });

  transition.ready.then(
    () => {
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
        { duration: REVEAL_DURATION_MS, easing: REVEAL_EASING, pseudoElement: "::view-transition-new(root)" }
      );
    },
    () => {
      // The transition was skipped (e.g. a second click); the theme is already applied.
    }
  );
}

/** Current theme; "light" during server rendering and hydration. */
export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, readTheme, () => "light");
}
