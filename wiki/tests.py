import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import WikiAttachment, WikiBlock, WikiCategory, WikiPage
from .text import markdown_to_blocks, render_inline, PAGE_TEMPLATES

User = get_user_model()


class TextTests(TestCase):
    def test_inline_markup_is_escaped_and_rendered(self):
        html = render_inline('<b>x</b> **fett** *kursiv* `code` [Link](https://example.org) http://auto.de', wiki_links=False)
        self.assertIn('&lt;b&gt;x&lt;/b&gt;', html)
        self.assertIn('<strong>fett</strong>', html)
        self.assertIn('<em>kursiv</em>', html)
        self.assertIn('<code', html)
        self.assertIn('href="https://example.org"', html)
        self.assertIn('href="http://auto.de"', html)
        self.assertNotIn('<a href="javascript', render_inline('[x](javascript:alert(1))', wiki_links=False))

    def test_wiki_links(self):
        user = User.objects.create_user(username='u', password='pw')
        page = WikiPage.objects.create(title='Atemschutz Prüfung', created_by=user, updated_by=user)
        html = render_inline('Siehe [[Atemschutz Prüfung]] und [[Gibt es nicht|Fehlt]]')
        self.assertIn(page.get_absolute_url(), html)
        self.assertIn('Fehlt', html)
        self.assertIn('gibt es noch nicht', html)

    def test_markdown_to_blocks(self):
        text = """# Titel
Absatz eins
weiter.

- a
- b
1. eins
2. zwei
- [ ] offen
- [x] erledigt
> Zitat
> [!WARNUNG] Vorsicht
```
code
```
| A | B |
|---|---|
| 1 | 2 |
![Bild](/media/x.png)
---
"""
        blocks = markdown_to_blocks(text)
        types = [b[0] for b in blocks]
        self.assertEqual(types, ['heading_1', 'paragraph', 'bullet_list', 'numbered_list', 'checklist', 'quote',
                                 'alert', 'code', 'table', 'image', 'divider'])
        self.assertEqual(blocks[1][1]['text'], 'Absatz eins\nweiter.')
        self.assertEqual([i['text'] for i in blocks[2][1]['items']], ['a', 'b'])
        self.assertTrue(blocks[4][1]['items'][1]['checked'])
        self.assertEqual(blocks[6][1]['type'], 'warning')
        self.assertEqual(blocks[8][1]['headers'], ['A', 'B'])
        self.assertEqual(blocks[8][1]['rows'], [['1', '2']])


class WikiViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='autor', password='pw')
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='wiki', codename__in=['view_wikipage', 'add_wikipage', 'change_wikipage',
                                                          'publish_wiki_page', 'view_internal_pages']))
        self.client.force_login(self.user)
        self.category = WikiCategory.objects.create(name='Anleitungen', slug='anleitungen', icon='📘')

    def _page(self, title='Pumpe bedienen', **kwargs):
        kwargs.setdefault('created_by', self.user)
        kwargs.setdefault('updated_by', self.user)
        kwargs.setdefault('status', WikiPage.STATUS_PUBLISHED)
        kwargs.setdefault('visibility', WikiPage.VISIBILITY_PUBLIC)
        kwargs.setdefault('category', self.category)
        return WikiPage.objects.create(title=title, **kwargs)

    def test_create_with_template_and_tags(self):
        response = self.client.post(reverse('wiki:page_create'), {
            'title': 'Drehleiter aufstellen', 'category': self.category.pk, 'parent': '', 'description': '',
            'visibility': 'public', 'tags_input': 'Drehleiter, Aufstellen', 'template': 'anleitung'})
        page = WikiPage.objects.get(title='Drehleiter aufstellen')
        self.assertRedirects(response, reverse('wiki:block_editor', args=[page.slug]))
        self.assertEqual(page.tags, ['Drehleiter', 'Aufstellen'])
        self.assertEqual(page.blocks.count(), len(PAGE_TEMPLATES['anleitung']['blocks']))
        self.assertTrue(page.blocks.filter(block_type='steps').exists())
        self.assertIn('Voraussetzungen', page.search_text)

    def test_search_finds_block_content(self):
        page = self._page()
        page.append_blocks([('paragraph', {'text': 'Die Kupplung vor dem Ansaugen prüfen.'}, {}),
                            ('steps', {'steps': [{'title': 'Saugleitung anschließen', 'text': '', 'image': ''}]}, {})])
        self._page(title='Anderes Thema').append_blocks([('paragraph', {'text': 'Nichts mit Wasser.'}, {})])
        response = self.client.get(reverse('wiki:search'), {'q': 'saugleitung kupplung'})
        self.assertContains(response, 'Pumpe bedienen')
        self.assertNotContains(response, 'Anderes Thema')
        self.assertContains(response, '1 Treffer')
        # Entwürfe anderer Nutzer bleiben unsichtbar
        other = User.objects.create_user(username='x', password='pw')
        self._page(title='Geheimer Entwurf', status=WikiPage.STATUS_DRAFT, created_by=other)
        response = self.client.get(reverse('wiki:search'), {'q': 'geheimer'})
        self.assertContains(response, '0 Treffer')

    def test_block_api_keeps_search_text_current(self):
        page = self._page()
        response = self.client.post(reverse('wiki:block_create', args=[page.slug]),
                                    json.dumps({'block_type': 'paragraph', 'content': {'text': 'Erstinhalt'}}),
                                    content_type='application/json')
        block_id = response.json()['block_id']
        page.refresh_from_db()
        self.assertIn('Erstinhalt', page.search_text)
        self.client.post(reverse('wiki:block_update', args=[page.slug, block_id]),
                         json.dumps({'content': {'text': 'Geändert'}}), content_type='application/json')
        page.refresh_from_db()
        self.assertIn('Geändert', page.search_text)
        self.assertNotIn('Erstinhalt', page.search_text)

    def test_upload_and_render(self):
        page = self._page()
        png = SimpleUploadedFile('foto.png', b'\x89PNG\r\n\x1a\n' + b'0' * 20, content_type='image/png')
        response = self.client.post(reverse('wiki:attachment_upload', args=[page.slug]), {'file': png})
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_image'])
        attachment = WikiAttachment.objects.get()
        page.append_blocks([('image', {'url': data['url'], 'alt': 'Foto', 'caption': 'Pumpe'}, {})])
        response = self.client.get(page.get_absolute_url())
        self.assertContains(response, data['url'])
        self.assertContains(response, 'Anhänge')
        response = self.client.post(reverse('wiki:attachment_delete', args=[page.slug, attachment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WikiAttachment.objects.exists())

    def test_markdown_import_append_and_replace_with_revision(self):
        page = self._page()
        page.append_blocks([('paragraph', {'text': 'alt'}, {})])
        response = self.client.post(reverse('wiki:markdown_import', args=[page.slug]),
                                    {'text': '# Neu\n\nText **fett**\n\n- a\n- b', 'mode': 'append'})
        self.assertRedirects(response, reverse('wiki:block_editor', args=[page.slug]))
        self.assertEqual([b.block_type for b in page.blocks.all()], ['paragraph', 'heading_1', 'paragraph', 'bullet_list'])
        self.client.post(reverse('wiki:markdown_import', args=[page.slug]), {'text': 'Nur das', 'mode': 'replace'})
        self.assertEqual([b.block_type for b in page.blocks.all()], ['paragraph'])
        self.assertEqual(page.revisions.count(), 1)  # Sicherung vor dem Ersetzen
        self.assertEqual(len(page.revisions.first().blocks_snapshot), 4)

    def test_revisions_restore_and_publish(self):
        page = self._page(status=WikiPage.STATUS_DRAFT)
        page.append_blocks([('paragraph', {'text': 'Version eins'}, {})])
        self.client.post(reverse('wiki:page_publish', args=[page.slug]))
        page.refresh_from_db()
        self.assertEqual(page.status, WikiPage.STATUS_PUBLISHED)
        self.assertEqual(page.revisions.count(), 1)
        page.replace_blocks([('paragraph', {'text': 'Version zwei'}, {})])
        response = self.client.get(reverse('wiki:revisions', args=[page.slug]))
        self.assertContains(response, 'Version 1')
        response = self.client.get(reverse('wiki:revision_detail', args=[page.slug, 1]))
        self.assertContains(response, 'Version eins')
        response = self.client.post(reverse('wiki:revision_restore', args=[page.slug, 1]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(page.blocks.get().content['text'], 'Version eins')
        self.assertEqual(page.revisions.count(), 2)  # Sicherung des Zwischenstands

    def test_detail_toc_children_related_and_pdf(self):
        parent = self._page(title='Handbuch Pumpen', tags=['Pumpe'])
        child = self._page(title='Kapitel 1', parent=parent)
        related = self._page(title='Pumpenwartung', tags=['pumpe'])
        parent.append_blocks([('heading_1', {'text': 'Einleitung'}, {}), ('paragraph', {'text': 'Siehe [[Pumpenwartung]]'}, {}),
                              ('heading_2', {'text': 'Details'}, {}),
                              ('numbered_list', {'items': [{'text': 'eins'}, {'text': 'zwei'}]}, {})])
        response = self.client.get(parent.get_absolute_url())
        self.assertContains(response, '#block-')
        self.assertContains(response, 'Unterseiten')
        self.assertContains(response, 'Kapitel 1')
        self.assertContains(response, 'Verwandte Seiten')
        self.assertContains(response, related.get_absolute_url())
        self.assertContains(response, '<ol class="list-decimal')
        response = self.client.get(child.get_absolute_url())
        self.assertContains(response, 'Handbuch Pumpen')  # Brotkrumen über die Elternseite
        response = self.client.get(reverse('wiki:page_pdf', args=[parent.slug]))
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_edit_permissions_for_reader(self):
        page = self._page()
        reader = User.objects.create_user(username='leser', password='pw')
        reader.user_permissions.add(Permission.objects.get(content_type__app_label='wiki', codename='view_wikipage'))
        self.client.force_login(reader)
        self.assertEqual(self.client.get(page.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse('wiki:markdown_import', args=[page.slug])).status_code, 403)
        self.assertEqual(self.client.post(reverse('wiki:attachment_upload', args=[page.slug]), {}).status_code, 403)
        response = self.client.get(reverse('wiki:revisions', args=[page.slug]))
        self.assertNotContains(response, 'Aktuellen Stand sichern')
