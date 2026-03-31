"""Widget Registry — in-memory Store für alle registrierten Widgets.

Ablauf:
1. Jedes Widget-Package ruft register() in seiner __init__.py auf.
2. create_app() importiert alle Widget-Packages (triggert register()).
3. sync_to_db() wird beim App-Start aufgerufen und stellt sicher,
   dass alle registrierten Widgets als WidgetType in der DB existieren.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.widgets.base import BaseWidget

_registry: dict[str, 'BaseWidget'] = {}


def register(widget: 'BaseWidget') -> None:
    """Registriert ein Widget in der Registry."""
    _registry[widget.key] = widget


def get(key: str) -> 'BaseWidget | None':
    """Gibt das Widget für einen Key zurück, oder None."""
    return _registry.get(key)


def get_all() -> list['BaseWidget']:
    """Gibt alle registrierten Widgets zurück."""
    return list(_registry.values())


def sync_to_db() -> None:
    """Stellt sicher, dass alle registrierten Widgets als WidgetType in der DB existieren.

    Neue Widgets werden angelegt, bestehende nicht verändert.
    Muss innerhalb eines App-Kontexts aufgerufen werden.
    """
    from app import db
    from app.models import WidgetType

    for widget in _registry.values():
        existing = WidgetType.query.filter_by(key=widget.key).first()
        if not existing:
            db.session.add(WidgetType(
                key=widget.key,
                display_name=widget.display_name,
                description=widget.description,
            ))
    db.session.commit()
