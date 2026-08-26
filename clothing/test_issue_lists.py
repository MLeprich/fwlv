"""
Tests für Ausgabelisten der Kleiderkammer: Vorlage → Liste je Person →
Abhaken bucht OUTGOING-Bewegung und mindert Bestand, Rücknahme bucht RETURN.
"""
from decimal import Decimal

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from clothing.assignments import open_issues
from clothing.models import (
    ClothingCategory,
    ClothingIssueList,
    ClothingIssueListItem,
    ClothingIssueTemplate,
    ClothingIssueTemplateItem,
    ClothingItem,
    ClothingSizeAssignment,
    ClothingStockMovement,
    ClothingType,
    IssueListStatus,
)
from core.models import User
from inventory_base.models import StockMovementType
from personnel.models import Person


@pytest.fixture
def editor(db):
    user = User.objects.create_user(username='kammer', password='x', first_name='Karla', last_name='Kammer')
    user.user_permissions.set(Permission.objects.filter(content_type__app_label__in=['clothing', 'personnel']))
    return user


@pytest.fixture
def person(editor):
    return Person.objects.create(
        first_name='Max', last_name='Muster', personnel_number='P-1',
        created_by=editor, updated_by=editor,
    )


@pytest.fixture
def artikel(editor):
    kategorie = ClothingCategory.objects.create(name='Dienstkleidung', code='DK', created_by=editor, updated_by=editor)

    def anlegen(nummer, name, typ, groesse, bestand):
        return ClothingItem.objects.create(
            item_number=nummer, name=name, category=kategorie, clothing_type=typ,
            size=groesse, quantity=Decimal(bestand), created_by=editor, updated_by=editor,
        )

    return {
        'hose_m': anlegen('KL-1', 'Diensthose', ClothingType.PANTS, 'm', 5),
        'hose_l': anlegen('KL-2', 'Diensthose', ClothingType.PANTS, 'l', 2),
        'hemd_m': anlegen('KL-3', 'Diensthemd', ClothingType.SHIRT, 'm', 10),
    }


@pytest.fixture
def vorlage(editor, artikel):
    vorlage = ClothingIssueTemplate.objects.create(name='Neueinstellung BF', created_by=editor, updated_by=editor)
    ClothingIssueTemplateItem.objects.create(template=vorlage, item=artikel['hose_m'], quantity=2, sort_order=10)
    ClothingIssueTemplateItem.objects.create(template=vorlage, item=artikel['hemd_m'], quantity=3, sort_order=20)
    return vorlage


def test_liste_aus_vorlage_uebernimmt_personengroesse(client, editor, person, artikel, vorlage):
    ClothingSizeAssignment.objects.create(person=person, clothing_type=ClothingType.PANTS, size='l')
    client.force_login(editor)

    response = client.post(reverse('clothing:issue_list_create'), {
        'template': vorlage.pk, 'title': '', 'person': person.pk,
        'issue_date': '2026-08-26', 'notes': '',
    })

    liste = ClothingIssueList.objects.get()
    assert response.status_code == 302 and response['Location'] == liste.get_absolute_url()
    assert liste.title == 'Neueinstellung BF'  # Titel aus Vorlage übernommen
    positionen = list(liste.items.all())
    assert [p.item for p in positionen] == [artikel['hose_l'], artikel['hemd_m']]  # Hose in L, Hemd ohne Größenwunsch
    assert [p.quantity for p in positionen] == [Decimal('2'), Decimal('3')]
    assert liste.status == IssueListStatus.OPEN


def test_abhaken_bucht_ausgabe_und_mindert_bestand(client, editor, person, artikel, vorlage):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, created_by=editor, updated_by=editor)
    liste.add_items_from_template(vorlage)
    hose = liste.items.get(item=artikel['hose_m'])

    response = client.post(reverse('clothing:issue_list_item_book', args=[hose.pk]), {'done': '1'})

    assert response.status_code == 200
    assert response['HX-Trigger'] == 'issueListChanged'
    hose.refresh_from_db()
    artikel['hose_m'].refresh_from_db()
    assert hose.is_done and hose.done_by == editor
    assert artikel['hose_m'].quantity == Decimal('3')
    bewegung = hose.movement
    assert bewegung.movement_type == StockMovementType.OUTGOING
    assert bewegung.person == person and bewegung.quantity == Decimal('2')
    # Personalakte sieht die Ausgabe
    offen = {row['item']: row['quantity'] for row in open_issues(person=person)}
    assert offen == {artikel['hose_m'].pk: Decimal('2')}
    liste.refresh_from_db()
    assert liste.status == IssueListStatus.PARTIAL


def test_alle_buchen_schliesst_liste_ab(client, editor, person, artikel, vorlage):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, created_by=editor, updated_by=editor)
    liste.add_items_from_template(vorlage)

    client.post(reverse('clothing:issue_list_book_all', args=[liste.pk]))

    liste.refresh_from_db()
    assert liste.status == IssueListStatus.COMPLETED and liste.completed_at is not None
    assert liste.items.filter(is_done=False).count() == 0
    assert ClothingStockMovement.objects.filter(person=person, movement_type=StockMovementType.OUTGOING).count() == 2


def test_unzureichender_bestand_blockiert_buchung(client, editor, person, artikel):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, created_by=editor, updated_by=editor)
    position = ClothingIssueListItem.objects.create(issue_list=liste, item=artikel['hose_l'], quantity=5)

    response = client.post(reverse('clothing:issue_list_item_book', args=[position.pk]), {'done': '1'})

    assert response.status_code == 200
    assert 'reicht nicht' in response.content.decode()
    position.refresh_from_db()
    assert not position.is_done
    artikel['hose_l'].refresh_from_db()
    assert artikel['hose_l'].quantity == Decimal('2')
    assert not ClothingStockMovement.objects.exists()


def test_ruecknahme_bucht_rueckgabe(client, editor, person, artikel):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, created_by=editor, updated_by=editor)
    position = ClothingIssueListItem.objects.create(issue_list=liste, item=artikel['hemd_m'], quantity=3)
    position.book(editor)
    artikel['hemd_m'].refresh_from_db()
    assert artikel['hemd_m'].quantity == Decimal('7')

    client.post(reverse('clothing:issue_list_item_book', args=[position.pk]), {})  # Checkbox abgewählt → kein 'done'

    position.refresh_from_db()
    artikel['hemd_m'].refresh_from_db()
    assert not position.is_done and position.movement is None
    assert artikel['hemd_m'].quantity == Decimal('10')
    assert ClothingStockMovement.objects.filter(movement_type=StockMovementType.RETURN, person=person).count() == 1
    assert list(open_issues(person=person)) == []
    liste.refresh_from_db()
    assert liste.status == IssueListStatus.OPEN


def test_groesse_und_menge_aenderbar_bis_ausgabe(client, editor, person, artikel):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, created_by=editor, updated_by=editor)
    position = ClothingIssueListItem.objects.create(issue_list=liste, item=artikel['hose_m'], quantity=1)

    client.post(reverse('clothing:issue_list_item_update', args=[position.pk]), {'item': artikel['hose_l'].pk, 'quantity': '2'})
    position.refresh_from_db()
    assert position.item == artikel['hose_l'] and position.quantity == Decimal('2')

    position.book(editor)
    response = client.post(reverse('clothing:issue_list_item_update', args=[position.pk]), {'item': artikel['hose_m'].pk})
    assert 'Bereits ausgegeben' in response.content.decode()
    position.refresh_from_db()
    assert position.item == artikel['hose_l']


def test_liste_mit_buchungen_nicht_loeschbar(client, editor, person, artikel):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, created_by=editor, updated_by=editor)
    ClothingIssueListItem.objects.create(issue_list=liste, item=artikel['hemd_m'], quantity=1).book(editor)

    response = client.post(reverse('clothing:issue_list_delete', args=[liste.pk]))

    assert response.status_code == 302
    assert ClothingIssueList.objects.filter(pk=liste.pk).exists()


def test_seiten_und_pdf_rendern(client, editor, person, artikel, vorlage):
    client.force_login(editor)
    liste = ClothingIssueList.objects.create(title='Test', person=person, template=vorlage, created_by=editor, updated_by=editor)
    liste.add_items_from_template(vorlage)

    for name, args in [
        ('clothing:issue_template_list', []),
        ('clothing:issue_template_detail', [vorlage.pk]),
        ('clothing:issue_template_create', []),
        ('clothing:issue_list_list', []),
        ('clothing:issue_list_create', []),
        ('clothing:issue_list_detail', [liste.pk]),
        ('clothing:issue_list_update', [liste.pk]),
        ('clothing:issue_list_status', [liste.pk]),
        ('personnel:detail', [person.pk]),
    ]:
        assert client.get(reverse(name, args=args)).status_code == 200, name

    pdf = client.get(reverse('clothing:issue_list_pdf', args=[liste.pk]))
    assert pdf.status_code == 200 and pdf['Content-Type'] == 'application/pdf'
    assert pdf.content.startswith(b'%PDF')
    vorlage_pdf = client.get(reverse('clothing:issue_template_pdf', args=[vorlage.pk]))
    assert vorlage_pdf.status_code == 200 and vorlage_pdf.content.startswith(b'%PDF')


def test_ohne_recht_kein_zugriff(client, db, person):
    leser = User.objects.create_user(username='leser', password='x')
    client.force_login(leser)
    assert client.get(reverse('clothing:issue_list_list')).status_code == 403
