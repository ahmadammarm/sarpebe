"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface RevealProps extends React.HTMLAttributes<HTMLElement> {
  as?: "div" | "section" | "li";
  /** Delay before the reveal starts, in milliseconds (use it to stagger siblings). */
  delay?: number;
}

/**
 * Fades and lifts its content in the first time it scrolls into view. Content stays fully
 * visible without JavaScript or with reduced motion (see the [data-reveal] rules in globals.css).
 */
export function Reveal({ as: Tag = "div", delay = 0, className, style, ...props }: RevealProps) {
  const ref = React.useRef<HTMLElement>(null);

  React.useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      element.dataset.visible = "true";
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          element.dataset.visible = "true";
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const Element = Tag as React.ElementType;
  return (
    <Element
      ref={ref}
      data-reveal
      className={cn(className)}
      style={{ transitionDelay: `${delay}ms`, ...style }}
      {...props}
    />
  );
}
