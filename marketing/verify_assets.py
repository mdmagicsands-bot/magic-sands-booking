import re
from pathlib import Path

from django.test import Client

MS = Path(__file__).resolve().parents[1] / "static" / "ms"
files = {str(p.relative_to(MS)).replace("\\", "/") for p in MS.rglob("*") if p.is_file()}

client = Client()
urls = set()
for path in ["/", "/about/", "/services/", "/destinations/", "/testimonials/", "/contact/"]:
    html = client.get(path).content.decode("utf-8", errors="ignore")
    for match in re.findall(r"/static/ms/([^\"'\s>)]+)", html):
        urls.add(match)

missing = sorted(u for u in urls if u not in files)
home = client.get("/").content.decode("utf-8", errors="ignore")
remote = sorted(set(re.findall(r"https?://[^\s\"'>]+\.(?:jpg|jpeg|png|svg|webp)", home)))
print("missing", len(missing))
for u in missing:
    print("MISSING", u)
print("remote_on_home", len(remote))
for u in remote:
    print("REMOTE", u)
