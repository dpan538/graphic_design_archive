import styles from "./DescriptionBlock.module.css";

/* Layer 4 — running description text. `cols` comes from content-fit
   (fitLayout.ts): 1 = a single measure, up to 4 for a long transcription. */
export default function DescriptionBlock({
  text,
  cols,
}: {
  text: string | null;
  cols: number;
}) {
  if (!text) return null;
  return (
    <p className={styles.descBody} data-cols={cols}>
      {text}
    </p>
  );
}
