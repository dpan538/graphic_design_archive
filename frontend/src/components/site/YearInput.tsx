"use client";

import { useEffect, useState, type InputHTMLAttributes } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "min" | "max"> & {
  value: number | null; min: number; max: number; onCommit: (value: number | null) => void;
};

// Keep unfinished keyboard input local; validate only when the reader commits it.
export default function YearInput({ value, min, max, onCommit, ...props }: Props) {
  const [draft, setDraft] = useState(String(value ?? ""));
  useEffect(() => setDraft(String(value ?? "")), [value]);
  const commit = () => {
    const number = Number(draft);
    const next = draft === "" || !Number.isFinite(number) ? null : Math.min(max, Math.max(min, Math.round(number)));
    setDraft(String(next ?? ""));
    if (next !== value) onCommit(next);
  };
  return <input {...props} value={draft} onChange={(event) => setDraft(event.target.value)} onBlur={commit}
    onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); event.currentTarget.blur(); } }} />;
}
