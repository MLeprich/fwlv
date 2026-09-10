"""
Import/Export Resource für Objektverwaltung (Objekt-Stammdaten).
Spaltenüberschriften in Deutsch, Nutzungsart als lesbarer Text.
"""

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import BuildingObject, ObjectStatus, UsageCategory


class BuildingObjectResource(resources.ModelResource):
    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        self._user = user

    object_number = fields.Field(attribute='object_number', column_name='objektnummer')
    name = fields.Field(attribute='name', column_name='bezeichnung')
    usage_type = fields.Field(attribute='usage_type', column_name='nutzungsart',
                              widget=ForeignKeyWidget(UsageCategory, field='name'))
    street = fields.Field(attribute='street', column_name='strasse')
    house_number = fields.Field(attribute='house_number', column_name='hausnummer')
    postal_code = fields.Field(attribute='postal_code', column_name='plz')
    city = fields.Field(attribute='city', column_name='ort')
    floor_count = fields.Field(attribute='floor_count', column_name='obergeschosse')
    basement_count = fields.Field(attribute='basement_count', column_name='untergeschosse')
    has_fire_alarm_system = fields.Field(attribute='has_fire_alarm_system', column_name='brandmeldeanlage')
    latitude = fields.Field(attribute='latitude', column_name='breitengrad')
    longitude = fields.Field(attribute='longitude', column_name='laengengrad')
    status = fields.Field(attribute='status', column_name='status')
    notes = fields.Field(attribute='notes', column_name='hinweise')

    class Meta:
        model = BuildingObject
        fields = (
            'id', 'object_number', 'name', 'usage_type',
            'street', 'house_number', 'postal_code', 'city',
            'floor_count', 'basement_count', 'has_fire_alarm_system',
            'latitude', 'longitude', 'status', 'notes',
        )
        export_order = fields
        import_id_fields = ['object_number']
        skip_unchanged = True
        report_skipped = True

    def dehydrate_status(self, obj):
        return obj.get_status_display()

    NUMERIC_COLUMNS = ('breitengrad', 'laengengrad', 'obergeschosse', 'untergeschosse')
    BOOLEAN_COLUMNS = ('brandmeldeanlage',)
    TRUE_STRINGS = {'1', 'true', 'wahr', 'ja', 'x', 'yes'}
    FALSE_STRINGS = {'0', 'false', 'falsch', 'nein', 'no'}

    def before_import_row(self, row, **kwargs):
        # Nutzungsart: Bezeichnung unabhängig von Groß-/Kleinschreibung zuordnen;
        # unbekannte Bezeichnungen führen zu einem verständlichen Fehler.
        if 'nutzungsart' in row:
            value = str(row['nutzungsart'] or '').strip()
            if value:
                match = UsageCategory.objects.filter(name__iexact=value).first()
                if match is None:
                    raise ValueError(
                        f'Nutzungsart „{value}“ ist unbekannt – bitte zuerst unter '
                        '„Nutzungsarten“ anlegen.'
                    )
                row['nutzungsart'] = match.name
            else:
                row['nutzungsart'] = ''

        # Status: lesbares Label oder Code; leer -> Aktiv.
        # Alte Vorlagen mit Spalte 'aktiv' (Ja/Nein) werden weiterhin verstanden.
        status_value = str(row.get('status') or '').strip()
        if not status_value and 'aktiv' in row:
            legacy = str(row['aktiv']).strip().lower()
            status_value = ObjectStatus.INACTIVE if legacy in self.FALSE_STRINGS else ObjectStatus.ACTIVE
        if status_value:
            label_to_code = {label.lower(): code for code, label in ObjectStatus.choices}
            row['status'] = label_to_code.get(status_value.lower(), status_value)
        else:
            row['status'] = ObjectStatus.ACTIVE

        # Leere Zahlenfelder -> None (sonst Decimal/Integer-Validierungsfehler)
        for col in self.NUMERIC_COLUMNS:
            if col in row and str(row[col]).strip() == '':
                row[col] = None

        # Boolean-Spalten robust normalisieren ('' -> False, da Felder nicht-nullable)
        for col in self.BOOLEAN_COLUMNS:
            if col in row:
                row[col] = '1' if str(row[col]).strip().lower() in self.TRUE_STRINGS else '0'

    def before_save_instance(self, instance, *args, **kwargs):
        # Audit-Felder beim CSV-Import befüllen (created_by/updated_by sind PROTECT)
        user = getattr(self, '_user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            if instance.created_by_id is None:
                instance.created_by = user
            instance.updated_by = user
