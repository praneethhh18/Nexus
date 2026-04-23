"""
One-shot: migrate hardcoded hex colors in frontend/src/**/*.jsx to design tokens.

Handles:
  - 6-char hex (#rrggbb)  → mapped CSS var
  - 8-char hex (#rrggbbaa) → color-mix(in srgb, <var> <pct>%, transparent)
  - Leaves brand/semantic one-offs alone (whatsapp green, cyan, pink, etc.)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path


# 6-char hex → token
TOKEN = {
    # text
    "#64748b": "var(--color-text-dim)",
    "#6b7280": "var(--color-text-dim)",
    "#475569": "var(--color-text-dim)",
    "#94a3b8": "var(--color-text-muted)",
    "#cbd5e1": "var(--color-text)",
    "#e2e8f0": "var(--color-text)",
    # surfaces
    "#0f172a": "var(--color-surface-1)",
    "#1e293b": "var(--color-surface-2)",
    "#1f2937": "var(--color-surface-2)",
    "#111827": "var(--color-bg)",
    "#0c1222": "var(--color-bg)",
    "#06080f": "var(--color-bg)",
    "#0a0e1a": "var(--color-bg)",
    "#060a14": "var(--color-bg)",
    "#0a0f1c": "var(--color-bg)",
    "#0f1e33": "var(--color-surface-2)",
    "#334155": "var(--color-border-strong)",
    # accent (emerald) — replace old blue brand + any equivalents
    "#3b82f6": "var(--color-accent)",
    "#2563eb": "var(--color-accent-hover)",
    "#1d4ed8": "var(--color-accent-hover)",
    "#1e40af": "var(--color-accent-hover)",
    # info (sky blue, for secondary signals)
    "#60a5fa": "var(--color-info)",
    "#93c5fd": "var(--color-info)",
    "#bfdbfe": "var(--color-info)",
    # ok (emerald-ish greens)
    "#22c55e": "var(--color-ok)",
    "#4ade80": "var(--color-ok)",
    "#16a34a": "var(--color-ok)",
    "#15803d": "var(--color-ok)",
    "#10b981": "var(--color-ok)",
    "#86efac": "var(--color-ok)",
    # warn
    "#f59e0b": "var(--color-warn)",
    "#fbbf24": "var(--color-warn)",
    "#d97706": "var(--color-warn)",
    # err
    "#f87171": "var(--color-err)",
    "#ef4444": "var(--color-err)",
    "#dc2626": "var(--color-err)",
    "#fca5a5": "var(--color-err)",
}

# Colors we deliberately leave alone (brand, semantic one-offs)
KEEP = {
    "#fff", "#ffffff", "#000", "#000000",
    "#a78bfa", "#c4b5fd", "#8b5cf6", "#7c3aed",  # violet palette — used for Reports badge
    "#25d366",                                     # WhatsApp
    "#22d3ee", "#67e8f9",                          # cyan — used for WhatIf
    "#ec4899", "#f472b6",                          # pink
    "#0f766e",                                     # specific teal
    "#7f1d1d",                                     # dark red fallback
    "#581c87",                                     # deep purple
}


HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _alpha_pct(hex_alpha: str) -> int:
    """Convert a 2-char hex alpha to a rounded percentage."""
    try:
        return max(1, round(int(hex_alpha, 16) / 255 * 100))
    except ValueError:
        return 100


def _map(match: re.Match) -> str:
    raw = match.group(0).lower()
    # 3-char hex — rarely used, skip
    if len(raw) == 4:
        return match.group(0)
    # 8-char hex → color-mix with alpha
    if len(raw) == 9:
        base = raw[:7]
        if base in KEEP:
            return match.group(0)
        pct = _alpha_pct(raw[7:9])
        mapped = TOKEN.get(base)
        if mapped:
            return f"color-mix(in srgb, {mapped} {pct}%, transparent)"
        # unknown base color — leave untouched (brand one-off)
        return match.group(0)
    # 6-char
    if raw in KEEP:
        return match.group(0)
    return TOKEN.get(raw, match.group(0))


def main() -> int:
    root = Path("frontend/src")
    if not root.exists():
        print("frontend/src not found — run from project root", file=sys.stderr)
        return 1

    changed = 0
    total_subs = 0
    for p in root.rglob("*.jsx"):
        text = p.read_text(encoding="utf-8")
        new_text, n = HEX_RE.subn(_map, text)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            changed += 1
            total_subs += n
            print(f"  {p.relative_to(root)}  ({n} subs)")
    print(f"\n{changed} file(s) updated, {total_subs} substitutions total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
