"""Verify rendered marketing pages only reference existing /static/ms/ assets."""
import re
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
django.setup()

from django.test import Client

MS = ROOT / "static" / "ms"
files = {str(p.relative_to(MS)).replace("\\", "/") for p in MS.rglob("*") if p.is_file()}

client = Client()
paths = ["/", "/about/", "/services/", "/destinations/", "/testimonials/", "/contact/"]
urls = set()
for path in paths:
    html = client.get(path).content.decode("utf-8", errors="ignore")
    urls.update(re.findall(r"/static/ms/([^\"'\\)\\s]+)", html))

missing = sorted(u for u in urls if u not in files)
print(f"Checked pages: {len(paths)}")
print(f"Unique static/ms URLs: {len(urls)}")
print(f"Missing on disk: {len(missing)}")
for u in missing:
    print(f"  MISSING  {u}")
if missing:
    sys.exit(1)
