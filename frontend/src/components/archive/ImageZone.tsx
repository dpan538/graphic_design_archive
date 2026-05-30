"use client";

import { useState } from "react";
import type { SurfaceImage } from "@/types/archive";
import { isRenderableImage } from "@/lib/layout";

/**
 * Image bay.
 *
 * Renderable (IMG01 / IMG03 with URL):
 *   – starts with default portrait ratio (3/4), resets to natural aspect ratio
 *     once the image loads so each image keeps its own proportions.
 *
 * Image-present but non-renderable (IMG00 / IMG02 / missing URL):
 *   – reserves the image bay and renders an empty rights/source frame.
 *
 * IMG04:
 *   – no image frame; text-only layouts should normally avoid ImageZone.
 */
export default function ImageZone({
  image,
  description,
  sourceName,
  className = "",
}: {
  image: SurfaceImage;
  /** Display description / summary — shown in the info fallback card. */
  description?: string;
  /** Human-readable source name. */
  sourceName?: string;
  className?: string;
}) {
  const [aspectRatio, setAspectRatio] = useState<string>("3 / 4");
  const [loaded, setLoaded] = useState(false);

  if (!isRenderableImage(image)) {
    if (image.state === "IMG04") {
      return null;
    }
    return (
      <div className={`image-bay image-bay--empty-frame ${className}`}>
        <div className="image-bay__hatch" aria-hidden />
        <div className="image-bay__empty-copy">
          <span className="image-bay__code">{image.state}</span>
          <span className="image-bay__source">
            {sourceName || "Source image withheld"}
          </span>
          <p className="image-bay__desc">
            {description ||
              "Image area reserved. Display is withheld until source-level rights and reuse evidence are reviewed."}
          </p>
          <span className="image-bay__note">
            View image at source
          </span>
        </div>
      </div>
    );
  }

  return (
    <figure className={`flex flex-col items-start ${className}`}>
      <div
        className="relative overflow-hidden w-full"
        style={{ aspectRatio, transition: "aspect-ratio 0.1s" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={image.url as string}
          alt={image.credit ?? "Source plate"}
          className="absolute inset-0 w-full h-full object-contain"
          style={{ opacity: loaded ? 1 : 0, transition: "opacity 0.15s" }}
          onLoad={(e) => {
            const img = e.currentTarget;
            if (img.naturalWidth && img.naturalHeight) {
              setAspectRatio(`${img.naturalWidth} / ${img.naturalHeight}`);
            }
            setLoaded(true);
          }}
        />
        {!loaded && (
          <div className="absolute inset-0 bg-paper-2 animate-pulse" />
        )}
      </div>
      {image.credit ? (
        <figcaption
          className="mt-1 w-full flex items-baseline justify-between gap-2 text-ink-soft"
          style={{ fontSize: "0.56rem" }}
        >
          <span className="label-caps shrink-0">Plate {image.state}</span>
          <span className="truncate">{image.credit}</span>
        </figcaption>
      ) : null}
    </figure>
  );
}
