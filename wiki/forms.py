"""
Wiki Forms
Formulare für das Wiki-Modul
"""

from django import forms
from .models import WikiCategory, WikiPage
from .text import PAGE_TEMPLATES

INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm'


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


class WikiPageForm(forms.ModelForm):
    """Seiten-Metadaten inkl. Schlagwörtern (Komma-getrennt) und übergeordneter Seite."""
    tags_input = forms.CharField(
        label='Schlagwörter', required=False,
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Atemschutz, Prüfung, Übergabe'}),
        help_text='Mit Komma trennen – helfen bei Suche und „Verwandte Seiten“'
    )

    class Meta:
        model = WikiPage
        fields = ['title', 'category', 'parent', 'description', 'status', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT}),
            'category': forms.Select(attrs={'class': INPUT}),
            'parent': forms.Select(attrs={'class': INPUT}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'status': forms.Select(attrs={'class': INPUT}),
            'visibility': forms.Select(attrs={'class': INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = WikiPage.objects.filter(is_deleted=False).order_by('title')
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['parent'].queryset = qs
        self.fields['parent'].empty_label = '– keine (oberste Ebene) –'
        self.fields['category'].queryset = WikiCategory.objects.filter(is_active=True).order_by('order', 'name')
        if self.instance.pk and self.instance.tags:
            self.initial['tags_input'] = ', '.join(self.instance.tags)

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        if parent and self.instance.pk:
            node = parent
            while node:
                if node.pk == self.instance.pk:
                    raise forms.ValidationError('Eine Seite kann nicht unter sich selbst einsortiert werden.')
                node = node.parent
        return parent

    def save(self, commit=True):
        self.instance.tags = [t.strip() for t in self.cleaned_data.get('tags_input', '').split(',') if t.strip()]
        return super().save(commit)


class WikiPageCreateForm(WikiPageForm):
    template = forms.ChoiceField(
        label='Vorlage', required=False, initial='leer',
        choices=[(key, f"{t['icon']} {t['label']}") for key, t in PAGE_TEMPLATES.items()],
        widget=forms.RadioSelect,
    )

    class Meta(WikiPageForm.Meta):
        fields = ['title', 'category', 'parent', 'description', 'visibility']


class MarkdownImportForm(forms.Form):
    MODE_CHOICES = (('append', 'An vorhandenen Inhalt anhängen'), ('replace', 'Vorhandenen Inhalt ersetzen'))
    text = forms.CharField(
        label='Text', widget=forms.Textarea(attrs={'class': INPUT + ' font-mono', 'rows': 18,
                                                   'placeholder': '# Überschrift\n\nAbsatz mit **fett** und *kursiv*.\n\n- Aufzählung\n1. Nummeriert\n- [ ] Checkliste\n\n> [!WARNUNG] Wichtiger Hinweis\n\n| Spalte | Wert |\n|---|---|\n| A | 1 |'}),
    )
    mode = forms.ChoiceField(label='Einfügen', choices=MODE_CHOICES, initial='append', widget=forms.RadioSelect)
