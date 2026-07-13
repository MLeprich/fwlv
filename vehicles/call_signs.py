"""
Funkrufnamen zuordnen, umhängen und freigeben.

Der Funkrufname ist eine Rolle, die zwischen Fahrzeugen wandert: geht ein Fahrzeug in
die Werkstatt, übernimmt das Ersatzfahrzeug den Namen. Das ist bewusst kein simples
Feld-Update, denn es müssen immer zwei Dinge zusammen passieren:

  1. Vehicle.call_sign (der aktuelle Stand, den 123 Stellen im System lesen)
  2. CallSignAssignment (die Historie: wer trug den Namen wann)

Wer stattdessen von Hand am Feld dreht, erzeugt eine Historie, die lügt. Deshalb geht
alles durch diese Funktionen – und zwar in einer Transaktion.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import CallSignAssignment, Vehicle


def current_assignment(vehicle):
    """Die aktuell gültige Zuordnung eines Fahrzeugs (oder None)."""
    return vehicle.call_sign_assignments.filter(valid_to__isnull=True).first()


def holder_of(call_sign):
    """Welches Fahrzeug trägt diesen Funkrufnamen gerade? (oder None)"""
    if not call_sign:
        return None
    return Vehicle.objects.filter(call_sign=call_sign).first()


def history_for(vehicle):
    """Vollständige Funkrufnamen-Historie eines Fahrzeugs, neueste zuerst."""
    return vehicle.call_sign_assignments.all()


def history_of_call_sign(call_sign):
    """Welche Fahrzeuge trugen diesen Funkrufnamen, neueste zuerst."""
    return (
        CallSignAssignment.objects
        .filter(call_sign=call_sign)
        .select_related('vehicle')
        .order_by('-valid_from', '-id')
    )


@transaction.atomic
def assign_call_sign(call_sign, vehicle, valid_from=None, reason='', user=None):
    """
    Weist `vehicle` den Funkrufnamen zu – und nimmt ihn dem bisherigen Träger ab.

    Der Kern des Umhängens: hatte ein anderes Fahrzeug den Namen, wird dessen Zuordnung
    zum Vortag geschlossen und sein `call_sign` freigegeben, bevor der neue Träger ihn
    bekommt. Ohne diese Reihenfolge schlägt die Unique-Constraint zu.

    Gibt die neue CallSignAssignment zurück.
    """
    call_sign = (call_sign or '').strip()
    if not call_sign:
        raise ValidationError('Es muss ein Funkrufname angegeben werden.')

    valid_from = valid_from or timezone.localdate()

    bisheriger = holder_of(call_sign)
    if bisheriger == vehicle:
        raise ValidationError(
            f'{vehicle.license_plate} trägt den Funkrufnamen "{call_sign}" bereits.'
        )

    # 1. Bisherigen Träger freiräumen (sonst kollidiert die Unique-Constraint)
    if bisheriger is not None:
        release_call_sign(bisheriger, valid_to=valid_from, reason=reason, user=user)

    # 2. Trägt das Zielfahrzeug schon einen ANDEREN Namen? Den gibt es damit ab.
    if vehicle.call_sign and vehicle.call_sign != call_sign:
        release_call_sign(vehicle, valid_to=valid_from, reason=reason, user=user)

    # 3. Neue Zuordnung öffnen und den aktuellen Stand am Fahrzeug nachziehen
    vehicle.call_sign = call_sign
    vehicle.updated_by = user
    vehicle.save(update_fields=['call_sign', 'updated_by', 'updated_at'])

    return CallSignAssignment.objects.create(
        call_sign=call_sign,
        vehicle=vehicle,
        valid_from=valid_from,
        reason=reason,
        created_by=user,
        updated_by=user,
    )


@transaction.atomic
def release_call_sign(vehicle, valid_to=None, reason='', user=None):
    """
    Nimmt dem Fahrzeug seinen Funkrufnamen ab (z.B. weil es in die Werkstatt geht).

    Das Fahrzeug steht danach ohne Funkrufnamen da – das dürfen dank des partiellen
    Unique-Index auch mehrere gleichzeitig sein. Die Historie behält, dass es ihn bis
    `valid_to` hatte.
    """
    valid_to = valid_to or timezone.localdate()

    offen = current_assignment(vehicle)
    if offen is not None:
        offen.valid_to = valid_to
        if reason and not offen.reason:
            offen.reason = reason
        offen.updated_by = user
        offen.save(update_fields=['valid_to', 'reason', 'updated_by', 'updated_at'])

    if vehicle.call_sign:
        vehicle.call_sign = ''
        vehicle.updated_by = user
        vehicle.save(update_fields=['call_sign', 'updated_by', 'updated_at'])

    return offen
