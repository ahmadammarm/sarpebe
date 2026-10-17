"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FASES, faseForGrade } from "@/lib/utils/fase";
import { cn } from "@/lib/utils";

/** Type a grade, see its Kurikulum Merdeka phase. Mirrors the "Fase" label shown across the app. */
export function FaseFinder() {
  const [grade, setGrade] = useState("");
  const match = faseForGrade(grade);
  const typed = grade.trim().length > 0;

  const message = match
    ? `Kelas ${grade.trim()} masuk Fase ${match.code} (${match.grades}, ${match.level}).`
    : typed
      ? "Ketik angka kelas antara 1 sampai 12."
      : "Ketik kelas Anda untuk melihat fasenya.";

  return (
    <div>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
        <div className="w-28 space-y-1.5">
          <Label htmlFor="fase-kelas">Kelas</Label>
          <Input
            id="fase-kelas"
            inputMode="numeric"
            maxLength={2}
            placeholder="9"
            value={grade}
            onChange={(event) => setGrade(event.target.value)}
            aria-describedby="fase-hasil"
          />
        </div>
        <p id="fase-hasil" aria-live="polite" className="pb-2 text-ink-soft">
          {message}
        </p>
      </div>

      <ol className="mt-6 grid grid-cols-2 gap-3 min-[480px]:grid-cols-3 lg:grid-cols-6" aria-label="Fase A sampai F">
        {FASES.map((fase) => {
          const selected = match?.code === fase.code;
          return (
            <li
              key={fase.code}
              aria-current={selected ? "true" : undefined}
              className={cn(
                "rounded-md border bg-sheet px-4 py-3 transition-colors duration-300",
                selected ? "border-ballpoint bg-wash" : "border-rule"
              )}
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-display text-3xl font-bold leading-none">{fase.code}</span>
                <span className="text-xs font-semibold text-ink-soft">{fase.level}</span>
              </div>
              <p className="mt-2 text-sm capitalize text-ink-soft">{fase.grades}</p>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
