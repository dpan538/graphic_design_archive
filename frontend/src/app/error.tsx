"use client";

export default function ReadPlatformError({ reset }: { error: Error; reset: () => void }) {
  return <main className="read-platform"><p className="read-platform__eyebrow">Read service</p><h1>That release could not be opened.</h1><p role="alert">The selected sealed release is unavailable or its integrity could not be verified. No fallback data has been shown.</p><button type="button" onClick={reset}>Try again</button></main>;
}
