"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type MarkProps = React.ComponentProps<"mark"> & {
  /**
   * Make the stroke draw itself: "load" when the page opens, "view" when it scrolls into view.
   * Without it the highlight is simply there.
   */
  draw?: "load" | "view";
  /** Delay before the stroke starts, in milliseconds. */
  delay?: number;
};

/** Highlighter stroke. Use for cited sources and at most one key phrase per screen. */
export function Mark({ draw, delay = 0, className, style, ...props }: MarkProps) {
  const ref = React.useRef<HTMLElement>(null);

  React.useEffect(() => {
    const element = ref.current;
    if (draw !== "view" || !element) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      element.dataset.inView = "true";
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          element.dataset.inView = "true";
          observer.disconnect();
        }
      },
      { threshold: 0.8 }
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [draw]);

  return (
    <mark
      ref={ref}
      data-draw={draw}
      className={cn("mark", draw && "mark-draw", className)}
      style={{ "--mark-delay": `${delay}ms`, ...style } as React.CSSProperties}
      {...props}
    />
  );
}
