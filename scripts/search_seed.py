from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "archive_seed.sqlite"


def search(query: str, limit: int = 12) -> list[tuple[str, str, str, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.create_function("rank", 1, lambda value: value)
        sql = """
        select
          d.seed_table,
          d.seed_id,
          d.title,
          snippet(search_docs_fts, 1, '[', ']', ' ... ', 18) as snippet,
          d.facets_json
        from search_docs_fts
        join search_docs d on d.rowid = search_docs_fts.rowid
        where search_docs_fts match ?
        order by bm25(search_docs_fts)
        limit ?
        """
        try:
            rows = conn.execute(sql, (query, limit)).fetchall()
        except sqlite3.OperationalError:
            quoted_query = '"' + query.replace('"', '""') + '"'
            rows = conn.execute(sql, (quoted_query, limit)).fetchall()
        return rows
    finally:
        conn.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/search_seed.py <query> [limit]")
        raise SystemExit(2)

    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    if not DB_PATH.exists():
        print(f"SQLite snapshot not found: {DB_PATH}")
        print("Run: python scripts/build_sqlite_snapshot.py")
        raise SystemExit(1)

    rows = search(query, limit)
    if not rows:
        print("No results")
        return

    for seed_table, seed_id, title, snippet, facets_json in rows:
        print(f"{seed_table}:{seed_id} | {title}")
        if snippet:
            print(f"  {snippet}")
        print()


if __name__ == "__main__":
    main()
