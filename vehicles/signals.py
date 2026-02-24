"""
Vehicle Signals
Auto-Erstellung von Lagerorten für Fahrzeuge
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


def _get_vehicle_parent(vehicle):
    """
    Ermittelt den passenden Parent-Lagerort für ein Fahrzeug.

    Strategie:
    1. Wenn home_location gesetzt → suche Fahrzeughalle darunter
    2. Wenn keine Fahrzeughalle → verwende home_location direkt
    3. Wenn kein home_location → suche erste Fahrzeughalle im System
    """
    from locations.models import Location, LocationType

    if vehicle.home_location_id:
        home = vehicle.home_location
        # Suche Fahrzeughalle unter dem Heimatstandort
        vehicle_hall = Location.objects.filter(
            parent=home,
            location_type=LocationType.VEHICLE_HALL,
            is_active=True,
        ).first()
        if vehicle_hall:
            return vehicle_hall
        return home

    # Fallback: erste Fahrzeughalle im System
    return Location.objects.filter(
        location_type=LocationType.VEHICLE_HALL,
        is_active=True,
    ).first()


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

    parent = _get_vehicle_parent(instance)

    Location.objects.create(
        parent=parent,
        name=instance.name,
        code=code,
        location_type=LocationType.VEHICLE,
        linked_vehicle=instance,
        is_active=True,
        description=f"Mobiler Lagerort: {instance.call_sign} ({instance.license_plate})",
        created_by_id=instance.created_by_id,
        updated_by_id=instance.updated_by_id,
    )
