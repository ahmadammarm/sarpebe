"use client";

import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Table } from "@/types/lesson-plan";

interface EditableTableProps {
  /** Unique within the page; prefixes every control id. */
  id: string;
  table: Table;
  onChange: (table: Table) => void;
  /** What a row is called in button labels, e.g. "kegiatan" or "kriteria". */
  rowName?: string;
}

/**
 * A table whose cells are all editable. The columns are fixed (the backend validates that every
 * row has one cell per column); rows can be added and removed.
 *
 * From `sm` up it is a real table. Below that each row becomes a card with a labelled field per
 * column, so nothing needs sideways scrolling on a phone.
 */
export function EditableTable({ id, table, onChange, rowName = "baris" }: EditableTableProps) {
  const setCell = (rowIndex: number, columnIndex: number, value: string) => {
    onChange({
      ...table,
      rows: table.rows.map((row, r) => (r === rowIndex ? row.map((cell, c) => (c === columnIndex ? value : cell)) : row)),
    });
  };

  const addRow = () => onChange({ ...table, rows: [...table.rows, table.columns.map(() => "")] });
  const removeRow = (rowIndex: number) => onChange({ ...table, rows: table.rows.filter((_, r) => r !== rowIndex) });

  const removeButton = (rowIndex: number, className?: string) => (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      className={`text-ink-soft hover:bg-margin-wash hover:text-margin-text ${className ?? ""}`}
      aria-label={`Hapus ${rowName} ${rowIndex + 1}`}
      onClick={() => removeRow(rowIndex)}
    >
      <Trash2 aria-hidden />
    </Button>
  );

  return (
    <div>
      {/* sm and up: one table */}
      <div className="hidden overflow-hidden rounded-md border border-rule-strong sm:block">
        <table className="w-full table-fixed border-collapse text-sm">
          <caption className="sr-only">{table.caption}</caption>
          <thead className="bg-wash text-left">
            <tr>
              {table.columns.map((column) => (
                <th key={column} scope="col" className="border-b border-rule-strong px-2 py-2 font-semibold">
                  {column}
                </th>
              ))}
              <th scope="col" className="w-10 border-b border-rule-strong">
                <span className="sr-only">Hapus</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b border-rule last:border-b-0 align-top">
                {row.map((cell, columnIndex) => (
                  <td key={columnIndex} className="p-1">
                    <Textarea
                      id={`${id}-d-${rowIndex}-${columnIndex}`}
                      aria-label={`${table.columns[columnIndex]}, ${rowName} ${rowIndex + 1}`}
                      rows={3}
                      value={cell}
                      onChange={(e) => setCell(rowIndex, columnIndex, e.target.value)}
                      className="px-2 py-1.5 text-sm"
                    />
                  </td>
                ))}
                <td className="p-1 text-center">{removeButton(rowIndex)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* below sm: one card per row */}
      <ul className="space-y-3 sm:hidden" aria-label={table.caption}>
        {table.rows.map((row, rowIndex) => (
          <li key={rowIndex} className="space-y-3 rounded-md border border-rule-strong p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold capitalize">
                {rowName} {rowIndex + 1}
              </span>
              {removeButton(rowIndex)}
            </div>
            {row.map((cell, columnIndex) => (
              <div key={columnIndex} className="space-y-1.5">
                <Label htmlFor={`${id}-m-${rowIndex}-${columnIndex}`}>{table.columns[columnIndex]}</Label>
                <Textarea
                  id={`${id}-m-${rowIndex}-${columnIndex}`}
                  rows={2}
                  value={cell}
                  onChange={(e) => setCell(rowIndex, columnIndex, e.target.value)}
                />
              </div>
            ))}
          </li>
        ))}
      </ul>

      <Button type="button" variant="outline" size="sm" className="mt-3" onClick={addRow}>
        <Plus aria-hidden />
        Tambah {rowName}
      </Button>
    </div>
  );
}
