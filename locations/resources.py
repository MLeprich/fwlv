"""
Import/Export Resources für Locations
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Location


class LocationResource(resources.ModelResource):
    """
    Resource für Location Import/Export
    """

    # Übergeordneter Standort (parent) als Name statt ID
    parent = fields.Field(
        column_name='übergeordneter_standort',
        attribute='parent',
        widget=ForeignKeyWidget(Location, 'name')
    )

    # Typ als lesbarer Name
    location_type = fields.Field(
        column_name='typ',
        attribute='location_type'
    )

    class Meta:
        model = Location
        fields = (
            'id',
            'name',
            'location_type',
            'parent',
            'description',
            'address',
            'capacity',
            'is_active',
        )
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True

    def dehydrate_location_type(self, location):
        """Exportiert Typ als lesbaren Namen"""
        return location.get_location_type_display()

    def dehydrate_parent(self, location):
        """Exportiert Parent als Namen statt ID"""
        return location.parent.name if location.parent else ''

    def before_import_row(self, row, **kwargs):
        """Konvertiert lesbaren Typ zurück zu Code"""
        # Mapping von deutschen Namen zu Codes
        type_mapping = {
            'Standort/Wache': 'site',
            'Gebäude': 'building',
            'Stellfläche/Außenbereich': 'area',
            'Raum': 'room',
            'Stellplatz': 'parking_spot',
            'Regal/Schrank': 'rack',
            'Schrank': 'cabinet',
            'Regalboden/Fach': 'shelf',
            'Schublade': 'drawer',
            'Box/Kiste': 'box',
            'Fahrzeug': 'vehicle',
            'Container': 'container',
        }

        if 'typ' in row and row['typ']:
            row['typ'] = type_mapping.get(row['typ'], row['typ'])
