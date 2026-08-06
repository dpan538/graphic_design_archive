"use client";

import { useEffect, useRef, useState } from "react";

const REPOSITORY_URL = "https://github.com/dpan538/graphic_design_archive";

const citations = [
  {
    style: "APA",
    text: "Modern Graphic Design History. (2026). Modern Graphic Design History: A rights-aware archive index (Version v48) [Data set and web application]. GitHub. https://github.com/dpan538/graphic_design_archive",
  },
  {
    style: "MLA",
    text: "Modern Graphic Design History. Modern Graphic Design History: A Rights-Aware Archive Index. Version v48, 2026, GitHub, https://github.com/dpan538/graphic_design_archive. Accessed 6 Aug. 2026.",
  },
  {
    style: "IEEE",
    text: "Modern Graphic Design History, “Modern Graphic Design History: A rights-aware archive index,” ver. v48, 2026. [Online]. Available: https://github.com/dpan538/graphic_design_archive. [Accessed: Aug. 6, 2026].",
  },
] as const;

export default function ProjectCitationPanel() {
  const [copied, setCopied] = useState<string | null>(null);
  const resetTimer = useRef<number | null>(null);

  useEffect(() => () => {
    if (resetTimer.current !== null) window.clearTimeout(resetTimer.current);
  }, []);

  async function copyCitation(style: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(style);
      if (resetTimer.current !== null) window.clearTimeout(resetTimer.current);
      resetTimer.current = window.setTimeout(
        () => setCopied((current) => current === style ? null : current),
        1800,
      );
    } catch {
      setCopied("Copy unavailable");
    }
  }

  return (
    <div className="project-citation-panel">
      <header>
        <div>
          <p className="label-caps">Project repository</p>
          <h3>Code, frozen payloads, and research method</h3>
        </div>
        <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">
          Open GitHub <span aria-hidden="true">↗</span>
        </a>
      </header>
      <div className="project-citation-panel__formats">
        {citations.map((citation) => (
          <article key={citation.style}>
            <div>
              <strong>{citation.style}</strong>
              <button
                type="button"
                onClick={() => void copyCitation(citation.style, citation.text)}
                aria-label={`Copy ${citation.style} citation`}
              >
                {copied === citation.style ? "Copied" : "Copy"}
              </button>
            </div>
            <p>{citation.text}</p>
          </article>
        ))}
      </div>
      <p className="sr-only" aria-live="polite">
        {copied === "Copy unavailable"
          ? "Citation copy is unavailable in this browser. Select the citation text manually."
          : copied
            ? `${copied} citation copied to clipboard.`
            : ""}
      </p>
    </div>
  );
}
