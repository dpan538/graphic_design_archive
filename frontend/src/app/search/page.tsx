import { redirect } from "next/navigation";

/** Search is no longer a standalone page; it expands in-shell on the right. */
export default function SearchPage() {
  redirect("/");
}
