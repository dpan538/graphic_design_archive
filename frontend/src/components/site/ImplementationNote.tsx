import { implementation } from "@/features/machine-reading/project";
export default function ImplementationNote() {
  return <section id="implementation" aria-labelledby="implementation-title">
    <h3 id="implementation-title">Project implementation</h3>
    {implementation.map(({ title, text }) => <p key={title}><strong>{title}. </strong>{text}</p>)}
    <p><a href="/about.md" rel="alternate" type="text/markdown">Read this explanation as Markdown</a> · <a href="/read-api">Public reading API</a></p>
  </section>;
}
