"""
Replace `[r[1] for r in conn.execute('PRAGMA table_info(t)').fetchall()]`
with `list_columns(conn, t)` across the production codebase. The PRAGMA
pattern silently breaks on Postgres (the wrapper translates PRAGMA to
SELECT 1, then `r[1]` IndexErrors). list_columns is backend-aware.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FILES = [
    "api/invoices.py",
    "api/tasks.py",
    "api/db_indexes.py",
    "api/routers/database.py",
    "api/routers/bant.py",
    "api/businesses.py",
    "api/crm.py",
    "api/documents.py",
    "api/seed_data.py",
    "api/notifications.py",
    "api/data_export.py",
]

# Match: [r[1] for r in <var>.execute(<quote>PRAGMA table_info(<expr>)<quote>).fetchall()]
# Allow f-string prefix and either quote style. <expr> can include {var} placeholders.
PATTERN = re.compile(
    r'''\[r\[1\] for r in (\w+)\.execute\(f?["']PRAGMA table_info\(([^)]+)\)["']\)\.fetchall\(\)\]''',
)


def add_list_columns_import(text: str) -> str:
    """Make sure list_columns is imported. Idempotent."""
    if "list_columns" in text:
        return text
    # Existing `from config.db import get_conn` line — extend it
    new_text, n = re.subn(
        r"^from config\.db import ([\w, ]+)$",
        lambda m: f"from config.db import {m.group(1)}, list_columns" if "list_columns" not in m.group(1) else m.group(0),
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n:
        return new_text
    # No existing config.db import — add one after a `from config.` import
    new_text, n = re.subn(
        r"^(from config\.\w+ import [^\n]+)$",
        r"\1\nfrom config.db import list_columns",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n:
        return new_text
    return text  # caller will need to add manually


def main():
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            print(f"  SKIP: {rel} (missing)")
            continue
        text = p.read_text(encoding="utf-8")
        matches = PATTERN.findall(text)
        if not matches:
            print(f"  [--] {rel}: no PRAGMA pattern found")
            continue

        def repl(m):
            conn_var = m.group(1)
            table_expr = m.group(2).strip()
            # If the original used f-string interpolation `{tbl}`, the curly braces
            # are already in the expression — pass it as-is via a Python expression.
            # Replace e.g. {tbl} with tbl, {USER_PROFILE_TABLE} with the variable.
            inner = re.sub(r"\{(\w+)\}", r"\1", table_expr)
            # If the remaining is a quoted literal, wrap it; if an identifier or var, no quotes.
            if inner.startswith("'") or inner.startswith('"'):
                return f"list_columns({conn_var}, {inner})"
            # If it contains spaces or punctuation it must already be a valid expr
            return f"list_columns({conn_var}, {inner!r})" if inner.replace("_", "").isalnum() and not inner[0].isdigit() and inner.isidentifier() is False else f"list_columns({conn_var}, {inner})"

        new_text = PATTERN.sub(repl, text)
        new_text = add_list_columns_import(new_text)

        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            print(f"  [OK] {rel}: {len(matches)} replacement(s)")
        else:
            print(f"  [--] {rel}: matched but no change")


if __name__ == "__main__":
    main()
