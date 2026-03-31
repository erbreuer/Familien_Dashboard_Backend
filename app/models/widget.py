"""Widget Models"""
from app import db


class WidgetType(db.Model):
    """WidgetType model - Defines available widget types"""
    __tablename__ = 'widget_types'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    family_widgets = db.relationship('FamilyWidget', back_populates='widget_type')

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'display_name': self.display_name,
            'description': self.description
        }

    def __repr__(self):
        return f'<WidgetType {self.key}>'


class FamilyWidget(db.Model):
    """FamilyWidget model - Widget instances enabled for a family"""
    __tablename__ = 'family_widgets'

    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey(
        'families.id', ondelete='CASCADE'), nullable=False)
    widget_type_id = db.Column(db.Integer, db.ForeignKey(
        'widget_types.id', ondelete='CASCADE'), nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)

    # Grid-Layout (frontend-seitig konfigurierbar, backend-seitig gespeichert)
    grid_col = db.Column(db.Integer, default=1)
    grid_row = db.Column(db.Integer, default=1)
    grid_pos_x = db.Column(db.Integer, default=0)
    grid_pos_y = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint(
        'family_id', 'widget_type_id', name='uq_family_widget_type'),)

    family = db.relationship('Family', back_populates='widgets')
    widget_type = db.relationship('WidgetType', back_populates='family_widgets')
    user_permissions = db.relationship(
        'WidgetUserPermission', back_populates='family_widget', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'family_id': self.family_id,
            'widget_type_id': self.widget_type_id,
            'widget_key': self.widget_type.key if self.widget_type else None,
            'is_enabled': self.is_enabled,
            'grid_col': self.grid_col,
            'grid_row': self.grid_row,
            'grid_pos_x': self.grid_pos_x,
            'grid_pos_y': self.grid_pos_y,
        }

    def __repr__(self):
        return f'<FamilyWidget family_id={self.family_id} widget_type={self.widget_type_id}>'


class WidgetUserPermission(db.Model):
    """WidgetUserPermission model - Per-user permissions for a widget within a family.

    Einträge werden automatisch angelegt wenn:
    - Ein User einer Familie beitritt (für alle aktiven Widgets)
    - Ein Admin ein Widget aktiviert (für alle Familienmitglieder)
    Die Defaults kommen aus BaseWidget.get_default_permissions(role_name).
    Ein Admin kann Einträge nachträglich per PUT-Route überschreiben.
    """
    __tablename__ = 'widget_user_permissions'

    id = db.Column(db.Integer, primary_key=True)
    family_widget_id = db.Column(db.Integer, db.ForeignKey(
        'family_widgets.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='CASCADE'), nullable=False)

    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint(
        'family_widget_id', 'user_id', name='uq_widget_user'),)

    family_widget = db.relationship('FamilyWidget', back_populates='user_permissions')
    user = db.relationship('User', back_populates='widget_permissions')

    def to_dict(self):
        return {
            'id': self.id,
            'family_widget_id': self.family_widget_id,
            'user_id': self.user_id,
            'can_view': self.can_view,
            'can_edit': self.can_edit,
        }

    def __repr__(self):
        return f'<WidgetUserPermission widget_id={self.family_widget_id} user_id={self.user_id}>'
