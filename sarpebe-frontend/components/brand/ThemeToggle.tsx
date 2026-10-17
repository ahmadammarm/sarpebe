"use client";

import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { setTheme, useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const theme = useTheme();
  const next = theme === "dark" ? "light" : "dark";

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={(event) => {
        // The new theme grows out of the button that was pressed.
        const box = event.currentTarget.getBoundingClientRect();
        setTheme(next, { x: box.left + box.width / 2, y: box.top + box.height / 2 });
      }}
      aria-label={next === "dark" ? "Ganti ke mode gelap" : "Ganti ke mode terang"}
      title={next === "dark" ? "Mode gelap" : "Mode terang"}
    >
      <span className="relative size-5" aria-hidden>
        <Sun
          className={cn(
            "absolute inset-0 size-5 transition-all duration-300",
            theme === "dark" ? "rotate-0 scale-100 opacity-100" : "rotate-90 scale-50 opacity-0"
          )}
        />
        <Moon
          className={cn(
            "absolute inset-0 size-5 transition-all duration-300",
            theme === "dark" ? "-rotate-90 scale-50 opacity-0" : "rotate-0 scale-100 opacity-100"
          )}
        />
      </span>
    </Button>
  );
}
