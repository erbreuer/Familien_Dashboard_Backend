"""Widget service"""
from app import db
from app.models import FamilyWidget, WidgetType, WidgetUserPermission


class WidgetService:

    @staticmethod
    def get_widgets_for_user(family_id: int, user_id: int) -> list[dict]:
        perms = (
            WidgetUserPermission.query
            .join(FamilyWidget)
            .join(WidgetType)
            .filter(
                FamilyWidget.family_id == family_id,
                WidgetUserPermission.user_id == user_id,
                WidgetUserPermission.can_view,
            )
            .all()
        )
        result = []
        for perm in perms:
            data = perm.family_widget.to_dict()
            data['display_name'] = perm.family_widget.widget_type.display_name
            data['description'] = perm.family_widget.widget_type.description
            data['can_edit'] = perm.can_edit
            result.append(data)
        return result

    @staticmethod
    def update_user_permission(
        family_id: int,
        family_widget_id: int,
        user_id: int,
        can_view: bool,
        can_edit: bool,
    ) -> WidgetUserPermission:
        family_widget = FamilyWidget.query.filter_by(
            id=family_widget_id, family_id=family_id
        ).first()
        if not family_widget:
            raise ValueError('Widget nicht gefunden')

        perm = WidgetUserPermission.query.filter_by(
            family_widget_id=family_widget_id, user_id=user_id
        ).first()
        if not perm:
            raise ValueError('Permission-Eintrag nicht gefunden')

        perm.can_view = can_view
        perm.can_edit = can_edit
        db.session.commit()
        return perm

    @staticmethod
    def update_layout(
        family_id: int,
        family_widget_id: int,
        grid_col: int,
        grid_row: int,
        grid_pos_x: int,
        grid_pos_y: int,
    ) -> FamilyWidget:
        family_widget = FamilyWidget.query.filter_by(
            id=family_widget_id, family_id=family_id
        ).first()
        if not family_widget:
            raise ValueError('Widget nicht gefunden')

        family_widget.grid_col = grid_col
        family_widget.grid_row = grid_row
        family_widget.grid_pos_x = grid_pos_x
        family_widget.grid_pos_y = grid_pos_y
        db.session.commit()
        return family_widget
