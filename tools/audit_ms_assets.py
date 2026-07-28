"""Audit static/ms asset references vs files on disk."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "static" / "ms"

files = {str(p.relative_to(MS)).replace("\\", "/") for p in MS.rglob("*") if p.is_file()}

refs = set()
for p in ROOT.rglob("*"):
    if p.suffix not in {".py", ".html"}:
        continue
    s = str(p)
    if "static\\ms" in s or "static/ms" in s or ".venv" in s or "node_modules" in s:
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'ms\(["\']([^"\']+)["\']\)', text):
        refs.add(m.group(1).lstrip("/"))
    for m in re.finditer(r"static 'ms/([^']+)'", text):
        refs.add(m.group(1))
    for m in re.finditer(r'/static/ms/([^"\'\)\s]+)', text):
        refs.add(m.group(1))

missing = sorted(r for r in refs if r not in files)
print(f"Files on disk: {len(files)}")
print(f"Referenced paths: {len(refs)}")
print(f"Missing: {len(missing)}")
for r in missing:
    print(f"  MISSING  {r}")

# suggest alternates for missing
print("\nSuggested alternates:")
for r in missing:
    name = Path(r).name
    alts = sorted(f for f in files if Path(f).name.lower() == name.lower())
    if alts:
        print(f"  {r} -> {alts[0]}")
