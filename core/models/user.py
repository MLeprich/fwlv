"""
Custom User Model für FLVS
Erweitert Django's AbstractUser mit feuerwehr-spezifischen Feldern
"""

from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User Model mit erweiterten Feldern für Feuerwehr-Personal
    """

    # Persönliche Informationen
    personnel_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Personalnummer",
        help_text="Eindeutige Personalnummer"
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Telefon",
        help_text="Telefonnummer"
    )

    mobile = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mobil",
        help_text="Mobilnummer"
    )

    # Organisatorische Zuordnung
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Abteilung",
        help_text="Abteilung/Einheit"
    )

    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Position/Funktion",
        help_text="Position oder Funktion in der Feuerwehr"
    )

    # 2FA Settings
    force_2fa = models.BooleanField(
        default=False,
        verbose_name="2FA Pflicht",
        help_text="Benutzer muss 2FA aktiviert haben"
    )

    # Password Change Requirement
    password_must_change = models.BooleanField(
        default=False,
        verbose_name="Passwort muss geändert werden",
        help_text="Benutzer muss bei nächster Anmeldung das Passwort ändern"
    )

    # Zeitbasierte Zugriffsbeschränkung (für spezielle Rollen)
    access_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Zugriff ab",
        help_text="Zugriff nur ab dieser Uhrzeit erlaubt"
    )

    access_end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Zugriff bis",
        help_text="Zugriff nur bis zu dieser Uhrzeit erlaubt"
    )

    # Profile Picture
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name="Profilbild"
    )

    # Zusätzliche Felder
    notes = models.TextField(
        blank=True,
        verbose_name="Notizen",
        help_text="Interne Notizen zum Benutzer"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am"
    )

    class Meta:
        verbose_name = "Benutzer"
        verbose_name_plural = "Benutzer"
        ordering = ['last_name', 'first_name']
        permissions = [
            ("manage_users", "Kann Benutzer verwalten"),
            ("assign_roles", "Kann Rollen zuweisen"),
            ("view_audit_log", "Kann Audit-Log einsehen"),
            ("system_configuration", "Kann Systemkonfiguration aendern"),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Neue Benutzer automatisch zur Gruppe "Standard-Nutzer" hinzufügen
        if is_new:
            try:
                standard_gruppe = Group.objects.get(name='Standard-Nutzer')
                self.groups.add(standard_gruppe)
            except Group.DoesNotExist:
                pass  # Gruppe existiert nicht, ignorieren

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.last_name}, {self.first_name}"
        return self.username

    def get_full_name(self):
        """Vollständiger Name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def has_time_based_access(self):
        """
        Prüft ob der Benutzer zeitbasierte Zugriffsbeschränkungen hat
        und ob der aktuelle Zeitpunkt innerhalb des erlaubten Zeitfensters liegt
        """
        if not (self.access_start_time and self.access_end_time):
            return True  # Keine Beschränkung

        from django.utils import timezone
        now = timezone.localtime(timezone.now()).time()

        if self.access_start_time <= self.access_end_time:
            # Normale Zeitspanne (z.B. 08:00 - 18:00)
            return self.access_start_time <= now <= self.access_end_time
        else:
            # Über Mitternacht (z.B. 22:00 - 06:00)
            return now >= self.access_start_time or now <= self.access_end_time

    def get_roles(self):
        """
        Gibt alle Rollen (Groups) des Benutzers zurück
        """
        return self.groups.all()

    def has_role(self, role_name):
        """
        Prüft ob der Benutzer eine bestimmte Rolle hat
        """
        return self.groups.filter(name=role_name).exists()

    def is_btm_authorized(self):
        """
        Prüft ob Benutzer für BTM-Bereich autorisiert ist
        """
        return self.has_role('BTM-Beauftragter') or self.has_role('Administrator')

    def requires_2fa(self):
        """
        Prüft ob 2FA erforderlich ist
        """
        # 2FA ist erforderlich wenn:
        # - force_2fa gesetzt ist ODER
        # - Benutzer ist BTM-Beauftragter ODER
        # - Benutzer ist Administrator
        return (
            self.force_2fa or
            self.has_role('BTM-Beauftragter') or
            self.has_role('Administrator')
        )
