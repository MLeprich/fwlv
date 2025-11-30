from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class DrivingLicenseClass(models.TextChoices):
    B = 'B', _('B (PKW)')
    BE = 'BE', _('BE (PKW mit Anhänger)')
    B96 = 'B96', _('B96 (PKW mit Anhänger bis 4,25t)')
    C = 'C', _('C (LKW)')
    CE = 'CE', _('CE (LKW mit Anhänger)')
    C1 = 'C1', _('C1 (LKW bis 7,5t)')
    C1E = 'C1E', _('C1E (LKW bis 7,5t mit Anhänger)')
    D = 'D', _('D (Bus)')
    DE = 'DE', _('DE (Bus mit Anhänger)')
    D1 = 'D1', _('D1 (Kleinbus)')
    D1E = 'D1E', _('D1E (Kleinbus mit Anhänger)')
    A = 'A', _('A (Motorrad)')
    A1 = 'A1', _('A1 (Leichtkraftrad)')
    A2 = 'A2', _('A2 (Motorrad bis 35 kW)')
    AM = 'AM', _('AM (Moped)')
    T = 'T', _('T (Traktor)')
    L = 'L', _('L (Land- und Forstwirtschaft)')


class DrivingLicenseCheck(models.Model):
    person = models.ForeignKey('personnel.Person', on_delete=models.CASCADE, related_name='driving_license_checks', verbose_name=_('Person'))
    check_date = models.DateField(verbose_name=_('Datum der Überprüfung'), help_text=_('Wann wurde der Führerschein kontrolliert?'))
    checked_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='performed_license_checks', verbose_name=_('Überprüft von'))
    license_presented = models.BooleanField(default=False, verbose_name=_('Führerschein vorgezeigt'), help_text=_('Wurde der physische Führerschein vorgelegt?'))
    
    has_class_B = models.BooleanField(default=False, verbose_name=_('Klasse B (PKW)'))
    has_class_BE = models.BooleanField(default=False, verbose_name=_('Klasse BE (PKW mit Anhänger)'))
    has_class_C = models.BooleanField(default=False, verbose_name=_('Klasse C (LKW)'))
    has_class_CE = models.BooleanField(default=False, verbose_name=_('Klasse CE (LKW mit Anhänger)'))
    has_class_C1 = models.BooleanField(default=False, verbose_name=_('Klasse C1 (LKW bis 7,5t)'))
    has_class_C1E = models.BooleanField(default=False, verbose_name=_('Klasse C1E (LKW bis 7,5t mit Anhänger)'))
    has_class_D = models.BooleanField(default=False, verbose_name=_('Klasse D (Bus)'))
    has_class_A = models.BooleanField(default=False, verbose_name=_('Klasse A (Motorrad)'))
    
    license_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Führerschein gültig bis'), help_text=_('Ablaufdatum des Führerscheindokuments'))
    
    class_c_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Klasse C/C1 gültig bis'), help_text=_('Befristung der Fahrerlaubnis für C/C1 (alle 5 Jahre)'))
    class_c_medical_check_date = models.DateField(null=True, blank=True, verbose_name=_('Ärztliche Untersuchung C/C1 vom'), help_text=_('Datum der letzten ärztlichen Untersuchung für C/C1'))
    class_c_medical_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Ärztliche Untersuchung C/C1 gültig bis'), help_text=_('Gültigkeit des ärztlichen Gutachtens für C/C1'))
    
    class_ce_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Klasse CE/C1E gültig bis'), help_text=_('Befristung der Fahrerlaubnis für CE/C1E (alle 5 Jahre)'))
    class_ce_medical_check_date = models.DateField(null=True, blank=True, verbose_name=_('Ärztliche Untersuchung CE/C1E vom'), help_text=_('Datum der letzten ärztlichen Untersuchung für CE/C1E'))
    class_ce_medical_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Ärztliche Untersuchung CE/C1E gültig bis'), help_text=_('Gültigkeit des ärztlichen Gutachtens für CE/C1E'))
    
    class_d_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Klasse D/D1 gültig bis'), help_text=_('Befristung der Fahrerlaubnis für D/D1'))
    class_d_medical_check_date = models.DateField(null=True, blank=True, verbose_name=_('Ärztliche Untersuchung D/D1 vom'), help_text=_('Datum der letzten ärztlichen Untersuchung für D/D1'))
    class_d_medical_expiry_date = models.DateField(null=True, blank=True, verbose_name=_('Ärztliche Untersuchung D/D1 gültig bis'), help_text=_('Gültigkeit des ärztlichen Gutachtens für D/D1'))
    
    notes = models.TextField(blank=True, verbose_name=_('Notizen'), help_text=_('Besonderheiten, Einschränkungen, etc.'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Führerscheinüberprüfung')
        verbose_name_plural = _('Führerscheinüberprüfungen')
        ordering = ['-check_date', 'person__last_name', 'person__first_name']
        indexes = [
            models.Index(fields=['person', '-check_date']),
            models.Index(fields=['check_date']),
            models.Index(fields=['license_presented']),
        ]

    def __str__(self):
        return f"{self.person} - {self.check_date}"

    def get_absolute_url(self):
        return reverse('driving_license:check_detail', kwargs={'pk': self.pk})

    def get_license_classes(self):
        classes = []
        if self.has_class_B:
            classes.append('B')
        if self.has_class_BE:
            classes.append('BE')
        if self.has_class_C:
            classes.append('C')
        if self.has_class_CE:
            classes.append('CE')
        if self.has_class_C1:
            classes.append('C1')
        if self.has_class_C1E:
            classes.append('C1E')
        if self.has_class_D:
            classes.append('D')
        if self.has_class_A:
            classes.append('A')
        return ', '.join(classes) if classes else _('Keine')

    def is_class_c_valid(self):
        from datetime import date
        if not self.has_class_C:
            return None
        if not self.class_c_expiry_date:
            return None
        return self.class_c_expiry_date >= date.today()

    def is_class_c_medical_valid(self):
        from datetime import date
        if not self.has_class_C:
            return None
        if not self.class_c_medical_expiry_date:
            return None
        return self.class_c_medical_expiry_date >= date.today()

    def is_class_ce_valid(self):
        from datetime import date
        if not self.has_class_CE:
            return None
        if not self.class_ce_expiry_date:
            return None
        return self.class_ce_expiry_date >= date.today()

    def is_class_ce_medical_valid(self):
        from datetime import date
        if not self.has_class_CE:
            return None
        if not self.class_ce_medical_expiry_date:
            return None
        return self.class_ce_medical_expiry_date >= date.today()

    @classmethod
    def get_latest_check_for_person(cls, person):
        return cls.objects.filter(person=person).order_by('-check_date').first()
