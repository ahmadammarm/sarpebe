import * as React from "react";
import { cn } from "@/lib/utils";

type SheetProps = React.ComponentProps<"div"> & {
  /** Adds the red margin rule and indents the content past it. */
  margin?: boolean;
};

/** A sheet of paper: the surface that content sits on. */
export function Sheet({ margin = false, className, ...props }: SheetProps) {
  return <div className={cn("sheet", margin && "sheet-margin", className)} {...props} />;
}
