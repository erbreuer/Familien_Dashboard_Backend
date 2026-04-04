"""Widget Registry — in-memory Store für alle registrierten Widgets.

Ablauf:
1. Jedes Widget-Package ruft register() in seiner __init__.py auf.
2. create_app() importiert alle Widget-Packages (triggert register()).
3. sync_to_db() wird beim App-Start aufgerufen und stellt sicher,
   dass alle registrierten Widgets als WidgetType in der DB existieren
   und für jede Familie FamilyWidget + WidgetUserPermission angelegt sind.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.widgets.base import BaseWidget

_registry: dict[str, 'BaseWidget'] = {}


def register(widget: 'BaseWidget') -> None:
    _registry[widget.key] = widget


def get(key: str) -> 'BaseWidget | None':
    return _registry.get(key)


def get_all() -> list['BaseWidget']:
    return list(_registry.values())


def sync_to_db() -> None:
    """Syncs WidgetTypes and provisions FamilyWidget + permissions for all families."""
    from app import db
    from app.models import WidgetType, FamilyWidget, WidgetUserPermission, Family, UserFamilyRole

    for widget in _registry.values():
        existing = WidgetType.query.filter_by(key=widget.key).first()
        if not existing:
            db.session.add(WidgetType(
                key=widget.key,
                display_name=widget.display_name,
                description=widget.description,
            ))
    db.session.flush()

    all_widget_types = WidgetType.query.all()
    all_families = Family.query.all()

    for family in all_families:
        existing_wt_ids = {
            fw.widget_type_id
            for fw in FamilyWidget.query.filter_by(family_id=family.id).all()
        }
        for wt in all_widget_types:
            if wt.id in existing_wt_ids:
                continue

            fw = FamilyWidget(family_id=family.id, widget_type_id=wt.id)
            db.session.add(fw)
            db.session.flush()

            widget_instance = _registry.get(wt.key)
            members = UserFamilyRole.query.filter_by(family_id=family.id).all()
            for member in members:
                role_name = member.role.name if member.role else 'Guest'
                defaults = (
                    widget_instance.get_default_permissions(role_name)
                    if widget_instance
                    else {'can_view': True, 'can_edit': False}
                )
                if role_name == 'Familyadmin':
                    defaults['can_view'] = True
                db.session.add(WidgetUserPermission(
                    family_widget_id=fw.id,
                    user_id=member.user_id,
                    can_view=defaults['can_view'],
                    can_edit=defaults['can_edit'],
                ))

    db.session.commit()
