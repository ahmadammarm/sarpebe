"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  /** What will happen, said plainly. */
  description: React.ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  /** Styles the confirm button as a destructive action. */
  destructive?: boolean;
  /** While true the dialog cannot be dismissed and the confirm button is disabled. */
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  /** Extra content between the description and the buttons, e.g. a password field. */
  children?: React.ReactNode;
}

/**
 * A modal confirmation built on the native <dialog>, so focus is trapped, Escape closes it and the
 * page behind is inert. The content is a form: Enter confirms, and fields in `children` belong to it.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "Batal",
  destructive = false,
  pending = false,
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  const ref = React.useRef<HTMLDialogElement>(null);
  const titleId = React.useId();
  const descriptionId = React.useId();

  React.useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const dismiss = () => {
    if (!pending) onCancel();
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      onCancel={(event) => {
        // Escape: let our state close it, so `open` and the element never disagree.
        event.preventDefault();
        dismiss();
      }}
      onClick={(event) => {
        // A click on the backdrop lands on the dialog element itself, not on its content.
        if (event.target === ref.current) dismiss();
      }}
      className="m-auto w-[calc(100%-2.5rem)] max-w-md rounded-md border border-rule bg-sheet p-0 text-foreground shadow-lg backdrop:bg-black/50"
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!pending) onConfirm();
        }}
        className="space-y-4 p-5 sm:p-6"
      >
        <h2 id={titleId} className="text-xl font-bold">
          {title}
        </h2>
        <div id={descriptionId} className="text-ink-soft [overflow-wrap:anywhere]">
          {description}
        </div>
        {children}
        <div className="flex flex-wrap justify-end gap-2 pt-1">
          <Button type="button" variant="outline" onClick={dismiss} disabled={pending}>
            {cancelLabel}
          </Button>
          <Button type="submit" variant={destructive ? "destructive" : "default"} disabled={pending}>
            {confirmLabel}
          </Button>
        </div>
      </form>
    </dialog>
  );
}
