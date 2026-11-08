import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page empty">
      <p>Ilyen oldal nincs. / This page does not exist.</p>
      <p><Link href="/hu" className="btn">Magyar</Link> <Link href="/en" className="btn">English</Link></p>
    </main>
  );
}
