"""Local static asset paths from the Hostinger export (static/ms/)."""

from pathlib import Path, PurePosixPath

MS_PREFIX = "ms"
MS_ROOT = Path(__file__).resolve().parents[1] / "static" / "ms"

# Common renames between theme backup paths and Laravel upload paths.
_ALIASES = {
    "images/testimonial/1.png": "uploads/testimonial/default.png",
    "images/testimonial/t4.png": "uploads/testimonial/default.png",
    "images/service/s1_1.jpg": "uploads/service/s1.jpg",
    "uploads/pages/about_2.jpg": "images/about-2.jpg",
    "uploads/pages/more/about_3.jpg": "images/about-3.jpg",
}


def ms(path: str) -> str:
    """Path served by Django static files under static/ms/."""
    return f"/static/{MS_PREFIX}/{path.lstrip('/')}"


def _exists(rel: str) -> bool:
    return (MS_ROOT / PurePosixPath(rel)).is_file()


def _pick_existing(*candidates: str) -> str:
    for rel in candidates:
        if not rel:
            continue
        rel = rel.lstrip("/")
        if rel in _ALIASES:
            rel = _ALIASES[rel]
        if _exists(rel):
            return ms(rel)
    return ""


def resolve_ms_url(value: str | None, *, default: str = "") -> str:
    """Map CMS/live URLs and relative paths to a local /static/ms/ URL."""
    if not value:
        return default

    raw = value.strip()
    if raw.startswith("/static/ms/"):
        return raw

    rel = raw
    if "://" in raw:
        for marker in ("/uploads/", "/assets/images/", "/assets/"):
            if marker in raw:
                rel = raw.split(marker, 1)[1]
                prefix = "uploads/" if marker == "/uploads/" else "images/"
                rel = f"{prefix}{rel}" if marker != "/assets/" else f"assets/{rel}"
                break
        else:
            return raw

    rel = rel.lstrip("/")
    if rel.startswith("assets/images/"):
        rel = rel.replace("assets/images/", "images/", 1)
    if rel.startswith("assets/"):
        rel = rel.replace("assets/", "", 1)

    resolved = _pick_existing(rel, _ALIASES.get(rel, ""))
    if resolved:
        return resolved

    # Theme backup often uses images/ while Laravel CMS uses uploads/.
    name = PurePosixPath(rel).name
    if rel.startswith("images/"):
        upload_guess = f"uploads/{PurePosixPath(rel).parent.name}/{name}"
        resolved = _pick_existing(upload_guess)
        if resolved:
            return resolved
    if rel.startswith("uploads/"):
        image_guess = f"images/{PurePosixPath(rel).parent.name}/{name}"
        resolved = _pick_existing(image_guess)
        if resolved:
            return resolved

    return default or ms(rel)
