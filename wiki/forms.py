"""
Wiki Forms
Formulare für das Wiki-Modul
"""

from django import forms
from .models import WikiCategory, WikiPage


class WikiCategoryForm(forms.ModelForm):
    """
    Formular für Wiki-Kategorien
    """
    class Meta:
        model = WikiCategory
        fields = ['name', 'icon', 'description', 'color', 'parent', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '📚'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'parent': forms.Select(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        help_texts = {
            'name': 'Name der Kategorie (z.B. "Einsatzpläne", "Anleitungen")',
            'icon': 'Emoji oder Icon für die Kategorie (z.B. 📋, 🔧, 🚒)',
            'description': 'Kurze Beschreibung der Kategorie',
            'color': 'Farbe für die Kategorie (Hex-Code)',
            'parent': 'Übergeordnete Kategorie (für Unterkategorien)',
            'order': 'Sortierreihenfolge (niedrigere Zahlen = weiter oben)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent circular parent relationships
        if self.instance.pk:
            self.fields['parent'].queryset = WikiCategory.objects.exclude(pk=self.instance.pk)
