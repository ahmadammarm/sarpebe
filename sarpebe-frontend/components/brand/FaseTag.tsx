import { faseForGrade } from "@/lib/utils/fase";
import { cn } from "@/lib/utils";

/** "Fase D" chip for a grade typed as a number; renders nothing for free-text grades. */
export function FaseTag({ grade, className }: { grade: string; className?: string }) {
  const fase = faseForGrade(grade);
  if (!fase) return null;

  return (
    <span
      title={`Fase ${fase.code} mencakup ${fase.grades}`}
      className={cn(
        "inline-flex items-center rounded-sm border border-ballpoint/30 bg-wash px-1.5 py-0.5 text-xs font-semibold text-ballpoint",
        className
      )}
    >
      Fase {fase.code}
    </span>
  );
}
