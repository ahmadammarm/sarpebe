"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type FieldProps = Omit<React.ComponentProps<"input">, "id"> & {
  id: string;
  label: string;
  /** Validation message; replaces the hint while present. */
  error?: string;
  /** Short help shown under the input. */
  hint?: React.ReactNode;
  /** Shown to the right of the label (e.g. a "forgot password" link). */
  labelAction?: React.ReactNode;
};

/** Label + input + hint/error, wired together for assistive technology. */
export function Field({ id, label, error, hint, labelAction, className, ...inputProps }: FieldProps) {
  const messageId = error ? `${id}-error` : hint ? `${id}-hint` : undefined;

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <Label htmlFor={id}>{label}</Label>
        {labelAction}
      </div>
      <Input id={id} aria-invalid={Boolean(error)} aria-describedby={messageId} {...inputProps} />
      {error ? (
        <p id={messageId} className="text-sm font-medium text-margin-text">
          {error}
        </p>
      ) : hint ? (
        <div id={messageId} className="text-sm text-ink-soft">
          {hint}
        </div>
      ) : null}
    </div>
  );
}

/** A password field with a button to reveal what was typed. */
export function PasswordField({ id, label, error, hint, labelAction, className, ...inputProps }: Omit<FieldProps, "type">) {
  const [visible, setVisible] = React.useState(false);
  const messageId = error ? `${id}-error` : hint ? `${id}-hint` : undefined;

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <Label htmlFor={id}>{label}</Label>
        {labelAction}
      </div>
      <div className="relative">
        <Input
          id={id}
          type={visible ? "text" : "password"}
          aria-invalid={Boolean(error)}
          aria-describedby={messageId}
          className="pr-11"
          {...inputProps}
        />
        <button
          type="button"
          onClick={() => setVisible((value) => !value)}
          aria-pressed={visible}
          aria-label={visible ? "Sembunyikan password" : "Tampilkan password"}
          className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-md text-ink-soft outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/40"
        >
          {visible ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
        </button>
      </div>
      {error ? (
        <p id={messageId} className="text-sm font-medium text-margin-text">
          {error}
        </p>
      ) : hint ? (
        <div id={messageId} className="text-sm text-ink-soft">
          {hint}
        </div>
      ) : null}
    </div>
  );
}
