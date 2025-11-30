"""
Permission Models
Erweiterte Berechtigungs-Modelle für zeitbasierte und delegierte Permissions
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import TimeStampedModel


class TimeBasedPermission(TimeStampedModel):
    """
    Zeitbasierte Berechtigungen für User
    Erlaubt zeitliche Beschränkung von Permissions (z.B. nur während Dienstzeiten)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_permissions',
        verbose_name="Benutzer"
    )

    permission = models.CharField(
        max_length=255,
        verbose_name="Permission",
        help_text="Permission-Code (z.B. 'medical.view_medication')"
    )

    # Zeitfenster (Tageszeit)
    valid_from_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Gültig ab (Uhrzeit)",
        help_text="z.B. 08:00 für Start der Dienstzeit"
    )

    valid_to_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Gültig bis (Uhrzeit)",
        help_text="z.B. 20:00 für Ende der Dienstzeit"
    )

    # Wochentage (JSON Array: [1,2,3,4,5] für Mo-Fr)
    valid_weekdays = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Gültige Wochentage",
        help_text="Liste von Wochentagen (1=Montag, 7=Sonntag). Leer = alle Tage"
    )

    # Datum-Bereich
    valid_from_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Gültig ab (Datum)",
        help_text="Permission erst ab diesem Datum gültig"
    )

    valid_to_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Gültig bis (Datum)",
        help_text="Permission nur bis zu diesem Datum gültig"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
        help_text="Kann deaktiviert werden ohne zu löschen"
    )

    reason = models.TextField(
        blank=True,
        verbose_name="Grund",
        help_text="Grund für die zeitliche Beschränkung"
    )

    class Meta:
        verbose_name = "Zeitbasierte Berechtigung"
        verbose_name_plural = "Zeitbasierte Berechtigungen"
        ordering = ['user', 'permission']
        indexes = [
            models.Index(fields=['user', 'permission', 'is_active']),
            models.Index(fields=['valid_from_date', 'valid_to_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.permission}"

    def clean(self):
        """Validierung"""
        # Datum-Bereich prüfen
        if self.valid_from_date and self.valid_to_date:
            if self.valid_from_date > self.valid_to_date:
                raise ValidationError(
                    "valid_from_date muss vor valid_to_date liegen"
                )

        # Wochentage prüfen
        if self.valid_weekdays:
            if not isinstance(self.valid_weekdays, list):
                raise ValidationError("valid_weekdays muss eine Liste sein")
            if not all(isinstance(day, int) and 1 <= day <= 7 for day in self.valid_weekdays):
                raise ValidationError(
                    "valid_weekdays muss Zahlen zwischen 1-7 enthalten"
                )

    def is_currently_valid(self):
        """
        Prüft ob Permission aktuell gültig ist

        Returns:
            bool: True wenn Permission aktuell gültig
        """
        if not self.is_active:
            return False

        now = timezone.now()
        current_date = now.date()
        current_time = now.time()
        current_weekday = now.isoweekday()

        # Datum-Check
        if self.valid_from_date and current_date < self.valid_from_date:
            return False
        if self.valid_to_date and current_date > self.valid_to_date:
            return False

        # Wochentag-Check
        if self.valid_weekdays and current_weekday not in self.valid_weekdays:
            return False

        # Zeit-Check
        if self.valid_from_time and self.valid_to_time:
            if self.valid_from_time <= self.valid_to_time:
                # Normale Zeitspanne (z.B. 08:00 - 18:00)
                if not (self.valid_from_time <= current_time <= self.valid_to_time):
                    return False
            else:
                # Über Mitternacht (z.B. 22:00 - 06:00)
                if not (current_time >= self.valid_from_time or current_time <= self.valid_to_time):
                    return False
        elif self.valid_from_time:
            if current_time < self.valid_from_time:
                return False
        elif self.valid_to_time:
            if current_time > self.valid_to_time:
                return False

        return True

    def get_validity_description(self):
        """
        Gibt eine lesbare Beschreibung der Gültigkeitsbedingungen zurück

        Returns:
            str: Beschreibung
        """
        parts = []

        if self.valid_from_date or self.valid_to_date:
            if self.valid_from_date and self.valid_to_date:
                parts.append(f"Zeitraum: {self.valid_from_date} bis {self.valid_to_date}")
            elif self.valid_from_date:
                parts.append(f"Ab: {self.valid_from_date}")
            elif self.valid_to_date:
                parts.append(f"Bis: {self.valid_to_date}")

        if self.valid_weekdays:
            weekday_names = {
                1: 'Mo', 2: 'Di', 3: 'Mi', 4: 'Do',
                5: 'Fr', 6: 'Sa', 7: 'So'
            }
            days = ', '.join(weekday_names[d] for d in sorted(self.valid_weekdays))
            parts.append(f"Wochentage: {days}")

        if self.valid_from_time or self.valid_to_time:
            if self.valid_from_time and self.valid_to_time:
                parts.append(f"Uhrzeit: {self.valid_from_time} - {self.valid_to_time}")
            elif self.valid_from_time:
                parts.append(f"Ab: {self.valid_from_time}")
            elif self.valid_to_time:
                parts.append(f"Bis: {self.valid_to_time}")

        return ' | '.join(parts) if parts else "Keine zeitliche Beschränkung"


class Delegation(TimeStampedModel):
    """
    Vertretungsregelungen (z.B. bei Urlaub/Krankheit)
    Erlaubt temporäre Delegation von Berechtigungen an andere User
    """

    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_given',
        verbose_name="Vertretener",
        help_text="Person die vertreten wird"
    )

    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_received',
        verbose_name="Vertreter",
        help_text="Person die vertritt"
    )

    # Zeitraum der Vertretung
    valid_from = models.DateTimeField(
        verbose_name="Gültig ab",
        help_text="Start der Vertretung"
    )

    valid_to = models.DateTimeField(
        verbose_name="Gültig bis",
        help_text="Ende der Vertretung"
    )

    # Welche Permissions werden delegiert?
    delegated_permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Delegierte Berechtigungen",
        help_text="Liste der delegierten Permission-Codes. Leer wenn alle."
    )

    # Oder: Alle Permissions delegieren?
    delegate_all_permissions = models.BooleanField(
        default=False,
        verbose_name="Alle Berechtigungen delegieren",
        help_text="Wenn aktiv: Vertreter erhält alle Rechte des Vertretenen"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
        help_text="Vertretung ist aktiv"
    )

    # Grund für Vertretung
    reason = models.TextField(
        blank=True,
        verbose_name="Grund",
        help_text="Grund der Vertretung (z.B. Urlaub, Krankheit)"
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name="Notizen",
        help_text="Zusätzliche Hinweise zur Vertretung"
    )

    # Genehmigung
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegations_approved',
        verbose_name="Genehmigt von",
        help_text="Vorgesetzter der die Vertretung genehmigt hat"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Genehmigt am"
    )

    class Meta:
        verbose_name = "Vertretung"
        verbose_name_plural = "Vertretungen"
        ordering = ['-valid_from']
        indexes = [
            models.Index(fields=['delegator', 'is_active']),
            models.Index(fields=['delegate', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]

    def __str__(self):
        return f"{self.delegate.username} vertritt {self.delegator.username}"

    def clean(self):
        """Validierung"""
        # Zeitraum prüfen
        if self.valid_from and self.valid_to:
            if self.valid_from >= self.valid_to:
                raise ValidationError(
                    "valid_from muss vor valid_to liegen"
                )

        # Delegator und Delegate dürfen nicht identisch sein
        if self.delegator_id and self.delegate_id:
            if self.delegator_id == self.delegate_id:
                raise ValidationError(
                    "Delegator und Delegate dürfen nicht identisch sein"
                )

        # Permissions prüfen
        if self.delegated_permissions and not isinstance(self.delegated_permissions, list):
            raise ValidationError("delegated_permissions muss eine Liste sein")

        # Entweder delegated_permissions ODER delegate_all_permissions
        if self.delegated_permissions and self.delegate_all_permissions:
            raise ValidationError(
                "Entweder spezifische Permissions oder alle Permissions delegieren"
            )

    def is_currently_valid(self):
        """
        Prüft ob Vertretung aktuell gültig ist

        Returns:
            bool: True wenn Vertretung aktuell aktiv
        """
        if not self.is_active:
            return False

        now = timezone.now()
        return self.valid_from <= now <= self.valid_to

    def has_permission(self, permission_code):
        """
        Prüft ob eine bestimmte Permission delegiert ist

        Args:
            permission_code (str): Permission-Code (z.B. 'medical.view_medication')

        Returns:
            bool: True wenn Permission delegiert ist
        """
        if not self.is_currently_valid():
            return False

        if self.delegate_all_permissions:
            return True

        return permission_code in self.delegated_permissions

    def get_remaining_time(self):
        """
        Gibt verbleibende Zeit der Vertretung zurück

        Returns:
            timedelta: Verbleibende Zeit oder None
        """
        if not self.is_currently_valid():
            return None

        now = timezone.now()
        return self.valid_to - now

    def approve(self, approver):
        """
        Vertretung genehmigen

        Args:
            approver (User): User der die Vertretung genehmigt
        """
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save(update_fields=['approved_by', 'approved_at'])

    def end_early(self):
        """Vertretung vorzeitig beenden"""
        self.is_active = False
        self.valid_to = timezone.now()
        self.save(update_fields=['is_active', 'valid_to'])


class ObjectPermission(TimeStampedModel):
    """
    Object-Level Permissions
    Ergänzt django-guardian für erweiterte Object-Permissions
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='object_permissions',
        verbose_name="Benutzer"
    )

    permission = models.CharField(
        max_length=255,
        verbose_name="Permission",
        help_text="Permission-Code"
    )

    # Generic Foreign Key würde hier verwendet werden
    # für echte Object-Level Permissions
    # Für jetzt: nur als Placeholder

    object_type = models.CharField(
        max_length=100,
        verbose_name="Objekttyp",
        help_text="z.B. 'location', 'order', etc."
    )

    object_id = models.PositiveIntegerField(
        verbose_name="Objekt-ID"
    )

    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='object_permissions_granted',
        verbose_name="Erteilt von"
    )

    reason = models.TextField(
        blank=True,
        verbose_name="Grund"
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Läuft ab am",
        help_text="Optional: Zeitpunkt wann Permission abläuft"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv"
    )

    class Meta:
        verbose_name = "Objekt-Berechtigung"
        verbose_name_plural = "Objekt-Berechtigungen"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'permission', 'is_active']),
            models.Index(fields=['object_type', 'object_id']),
        ]
        unique_together = [
            ['user', 'permission', 'object_type', 'object_id']
        ]

    def __str__(self):
        return f"{self.user.username} - {self.permission} on {self.object_type}:{self.object_id}"

    def is_currently_valid(self):
        """Prüft ob Permission aktuell gültig ist"""
        if not self.is_active:
            return False

        if self.expires_at and timezone.now() > self.expires_at:
            return False

        return True
