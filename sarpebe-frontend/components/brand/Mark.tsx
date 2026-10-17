import * as React from "react";
import { cn } from "@/lib/utils";

/** Highlighter stroke. Use for cited sources and at most one key phrase per screen. */
export function Mark({ className, ...props }: React.ComponentProps<"mark">) {
  return <mark className={cn("mark", className)} {...props} />;
}
