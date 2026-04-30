"""Replace sqlite_master patterns with portable helpers from config.db."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (filename, [(old, new), ...])
EDITS = {
    "api/db_indexes.py": [
        (
            'conn.execute("SELECT 1 FROM sqlite_master WHERE type=\'table\' AND name = ?", (name,)).fetchone()',
            "(table_exists(conn, name) and (1,) or None)",
        ),
    ],
    "api/data_export.py": [
        (
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1",
            None,  # handled via inline replacement below
        ),
    ],
    "api/onboarding.py": [],
    "api/reliability.py": [],
    "api/routers/database.py": [],
    "sql_agent/data_import.py": [],
    "utils/whatif_simulator.py": [],
}


def main():
    """Manual targeted replacements per file. Easier to audit than regex."""
    edits = {
        "api/db_indexes.py": (
            "exists = conn.execute(\n        \"SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?\", (name,),\n    ).fetchone()",
            "exists = table_exists(conn, name)",
        ),
        "api/data_export.py": (
            'conn.execute(\n        "SELECT 1 FROM sqlite_master WHERE type=\'table\' AND name = ? LIMIT 1",\n        (name,),\n    ).fetchone()',
            "(1,) if table_exists(conn, name) else None",
        ),
        "api/onboarding.py": (
            'conn.execute(\n                    "SELECT COUNT(*) FROM sqlite_master WHERE type=\'table\' AND name LIKE \'imported_%\'"\n                ).fetchone()[0]',
            'sum(1 for t in list_tables(conn) if t.startswith("imported_"))',
        ),
        "api/reliability.py": (
            'conn.execute(\n            "SELECT COUNT(*) FROM sqlite_master WHERE type=\'table\'"\n        ).fetchone()[0]',
            "len(list_tables(conn))",
        ),
        "sql_agent/data_import.py": (
            'tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type=\'table\' ORDER BY name").fetchall()]',
            "tables = list_tables(conn)",
        ),
        "utils/whatif_simulator.py": (
            'conn.execute(\n        "SELECT 1 FROM sqlite_master WHERE type=\'table\' AND name=?", (name,),\n    ).fetchone()',
            "(1,) if table_exists(conn, name) else None",
        ),
    }

    for rel, (old, new) in edits.items():
        p = ROOT / rel
        if not p.exists():
            print(f"  SKIP: {rel}")
            continue
        text = p.read_text(encoding="utf-8")
        if old in text:
            text = text.replace(old, new)
            # Add list_tables / table_exists to the import line
            for needed in ("table_exists", "list_tables"):
                if needed in new and needed not in text.split(chr(10), 200)[0:200]:
                    # crude scan — re-check
                    if f"from config.db import" in text and needed not in text.split("from config.db import", 1)[1].split(chr(10), 1)[0]:
                        text = re.sub(
                            r"^from config\.db import ([\w, ]+)$",
                            lambda m: f"from config.db import {m.group(1).strip()}, {needed}",
                            text,
                            count=1,
                            flags=re.MULTILINE,
                        )
            p.write_text(text, encoding="utf-8")
            print(f"  [OK] {rel}")
        else:
            print(f"  [--] {rel}: pattern not found (may need manual edit)")


if __name__ == "__main__":
    main()
