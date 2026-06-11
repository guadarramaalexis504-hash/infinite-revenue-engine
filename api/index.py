"""Vercel Python entrypoint for the Infinite Revenue tracking app.

Vercel's Python runtime looks for a module-level ``app`` (WSGI/ASGI callable).
We re-export the WSGI application from ``farm_loop.http_app`` and make the repo
root importable so ``farm_loop`` resolves when the function cold-starts.

Routing (e.g. /click, /webhooks/buymeacoffee) is handled inside the WSGI app
itself; vercel.json rewrites every path to this function so PATH_INFO is
preserved.
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from farm_loop.http_app import application as app  # noqa: E402

__all__ = ["app"]
