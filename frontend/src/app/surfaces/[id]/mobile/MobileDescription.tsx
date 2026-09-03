import styles from "./MobileDescription.module.css";

/* Layer 4, mobile — one measure, no columns. */
export default function MobileDescription({ text }: { text: string }) {
  return <p className={styles.body}>{text}</p>;
}
