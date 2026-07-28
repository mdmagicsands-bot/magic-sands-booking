"""Resolve which public surface this process serves."""

from __future__ import annotations

import os


def resolve_site_profile(*, on_railway: bool) -> str:
    """
    Return ``marketing`` or ``full``.

    Railway defaults to marketing-only until the booking app has its own repo
    and Railway service. Local dev defaults to full (marketing + booking).
    """
    raw = os.getenv("SITE_PROFILE", "").strip().lower()
    if raw in {"marketing", "full"}:
        return raw
    if on_railway:
        return "marketing"
    return "full"
