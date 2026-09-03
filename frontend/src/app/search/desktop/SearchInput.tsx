"use client";

import { useEffect, useRef } from "react";
import { Search as SearchIcon, X } from "lucide-react";
import styles from "./SearchInput.module.css";

export default function SearchInput({
  value,
  onChange,
  onClear,
}: {
  value: string;
  onChange: (q: string) => void;
  onClear: () => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);

  return (
    <div className={styles.wrap}>
      <SearchIcon size={20} strokeWidth={3} aria-hidden="true" />
      <input
        ref={ref}
        className={styles.input}
        type="search"
        placeholder="Find an object…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Search query"
      />
      {value ? (
        <button type="button" className={styles.clr} onClick={onClear} aria-label="Clear query">
          <X size={16} strokeWidth={3} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}
