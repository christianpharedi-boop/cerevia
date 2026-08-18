"""Thin HTTP interface over frozen CEREVIA protocol contracts."""

from .app import app, create_app

__all__ = ["app", "create_app"]
