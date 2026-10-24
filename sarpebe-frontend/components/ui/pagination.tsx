import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PaginationProps {
  /** Zero-based index of the current page. */
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  /** Accessible name of the navigation landmark. */
  label?: string;
  className?: string;
}

/** Previous and next buttons with a "Halaman N dari M" caption. Renders nothing for a single page. */
export function Pagination({ page, pageCount, onPageChange, label = "Halaman daftar", className }: PaginationProps) {
  if (pageCount <= 1) return null;

  return (
    <nav
      aria-label={label}
      className={cn("flex flex-wrap items-center justify-between gap-3 border-t border-rule py-4 text-sm text-ink-soft", className)}
    >
      <span>
        Halaman {page + 1} dari {pageCount}
      </span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={page === 0} onClick={() => onPageChange(page - 1)}>
          <ChevronLeft aria-hidden />
          Sebelumnya
        </Button>
        <Button variant="outline" size="sm" disabled={page + 1 >= pageCount} onClick={() => onPageChange(page + 1)}>
          Berikutnya
          <ChevronRight aria-hidden />
        </Button>
      </div>
    </nav>
  );
}
