"""
Core Forms für FLVS
Formulare für Benutzerprofil, Einstellungen, etc.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import UserSettings

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    """
    Formular für Benutzerprofil-Bearbeitung
    """

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'mobile',
            'profile_picture',
            'department',
            'position',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Vorname'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Nachname'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': '+49 123 456789'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': '+49 160 123456'
            }),
            'department': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'z.B. Einsatzabteilung'
            }),
            'position': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'z.B. Gruppenführer'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }
        labels = {
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'email': 'E-Mail',
            'phone': 'Telefon',
            'mobile': 'Mobil',
            'profile_picture': 'Profilbild',
            'department': 'Abteilung',
            'position': 'Position/Funktion',
        }
        help_texts = {
            'email': 'Diese E-Mail-Adresse wird für Benachrichtigungen verwendet.',
            'phone': 'Festnetznummer (optional)',
            'mobile': 'Mobilnummer (optional)',
            'profile_picture': 'Maximale Dateigröße: 2 MB. Erlaubt: JPG, PNG',
        }

    def clean_profile_picture(self):
        """Validierung Profilbild"""
        picture = self.cleaned_data.get('profile_picture')

        if picture:
            # Dateigröße prüfen (max 2 MB)
            if picture.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Die Datei ist zu groß. Maximale Größe: 2 MB.')

            # Dateityp prüfen
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
            if hasattr(picture, 'content_type') and picture.content_type not in allowed_types:
                raise forms.ValidationError('Ungültiger Dateityp. Erlaubt: JPG, PNG')

        return picture


class AccountSettingsForm(forms.ModelForm):
    """
    Account-Einstellungen (E-Mail, Sprache, Zeitzone)
    """

    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'email@example.com'
            }),
        }
        labels = {
            'email': 'E-Mail-Adresse',
        }

    language = forms.ChoiceField(
        choices=UserSettings.LANGUAGE_CHOICES,
        required=False,
        label='Sprache',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
        })
    )

    timezone = forms.CharField(
        required=False,
        label='Zeitzone',
        widget=forms.Select(
            choices=[('Europe/Berlin', 'Europe/Berlin (CET/CEST)'), ('UTC', 'UTC')],
            attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }
        )
    )


class NotificationSettingsForm(forms.ModelForm):
    """
    Benachrichtigungs-Einstellungen
    """

    class Meta:
        model = UserSettings
        fields = [
            'email_notifications',
            'email_critical_alerts',
            'email_weekly_summary',
            'push_enabled',
            'notify_critical_stock',
            'notify_expiring_items',
            'notify_upcoming_inspections',
            'notify_orders',
            'notify_vehicle_handover',
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'email_critical_alerts': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'email_weekly_summary': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'push_enabled': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'notify_critical_stock': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'notify_expiring_items': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'notify_upcoming_inspections': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'notify_orders': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'notify_vehicle_handover': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
        }


class AppearanceSettingsForm(forms.ModelForm):
    """
    Darstellungs-Einstellungen
    """

    class Meta:
        model = UserSettings
        fields = [
            'theme',
            'sidebar_behavior',
            'items_per_page',
            'table_density',
            'show_hints',
            'show_breadcrumbs',
            'compact_mode',
        ]
        widgets = {
            'theme': forms.RadioSelect(attrs={
                'class': 'text-primary-600 focus:ring-primary-500'
            }),
            'sidebar_behavior': forms.RadioSelect(attrs={
                'class': 'text-primary-600 focus:ring-primary-500'
            }),
            'items_per_page': forms.Select(attrs={
                'class': 'w-48 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'table_density': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'show_hints': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'show_breadcrumbs': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'compact_mode': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
        }


class PrivacySettingsForm(forms.ModelForm):
    """
    Datenschutz-Einstellungen
    """

    class Meta:
        model = UserSettings
        fields = [
            'analytics_enabled',
            'error_reporting',
        ]
        widgets = {
            'analytics_enabled': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
            'error_reporting': forms.CheckboxInput(attrs={
                'class': 'mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            }),
        }


class PasswordChangeCustomForm(forms.Form):
    """
    Passwort ändern Formular (Custom)
    """
    old_password = forms.CharField(
        label='Aktuelles Passwort',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Aktuelles Passwort eingeben'
        })
    )

    new_password1 = forms.CharField(
        label='Neues Passwort',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Neues Passwort eingeben'
        }),
        help_text='Mindestens 8 Zeichen, inkl. Buchstaben und Zahlen'
    )

    new_password2 = forms.CharField(
        label='Passwort wiederholen',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Neues Passwort wiederholen'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """Validierung altes Passwort"""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Das aktuelle Passwort ist falsch.')
        return old_password

    def clean(self):
        """Validierung Passwort-Übereinstimmung"""
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError('Die Passwörter stimmen nicht überein.')

        return cleaned_data

    def save(self, commit=True):
        """Passwort speichern"""
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


