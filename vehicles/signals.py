"""
Vehicle Signals
Auto-Erstellung von Lagerorten für Fahrzeuge
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='vehicles.Vehicle')
def ensure_vehicle_location(sender, instance, **kwargs):
    """
    Stellt sicher, dass jedes aktive Fahrzeug einen verknüpften Lagerort hat.
    Erstellt automatisch einen Location-Eintrag vom Typ 'vehicle'.
    """
    from locations.models import Location, LocationType

    if not instance.is_active:
        return

    # Prüfe ob bereits ein Lagerort existiert
    if Location.objects.filter(linked_vehicle=instance).exists():
        return

    # Code aus Kennzeichen generieren (Leerzeichen/Sonderzeichen entfernen)
    code = f"FZG-{instance.license_plate}".replace(' ', '-')

    # Sicherstellen, dass der Code eindeutig ist
    if Location.objects.filter(code=code).exists():
        code = f"FZG-{instance.pk}-{instance.license_plate}".replace(' ', '-')

    Location.objects.create(
        name=instance.name,
        code=code,
        location_type=LocationType.VEHICLE,
        linked_vehicle=instance,
        is_active=True,
        description=f"Mobiler Lagerort: {instance.call_sign} ({instance.license_plate})",
        created_by_id=instance.created_by_id,
        updated_by_id=instance.updated_by_id,
    )
