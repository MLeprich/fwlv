"""
Shared pytest-Fixtures für die idcards-Tests.
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from idcards.models import IdCardTemplate
from organization.models import Department, VolunteerUnit
from personnel.models import Person


User = get_user_model()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='admin_idc',
        email='admin_idc@example.test',
        password='pw',
        is_superuser=True,
        is_staff=True,
    )
    return user


@pytest.fixture
def manager_user(db):
    """User mit nur idcards.manage_idcards Permission (kein Superuser)."""
    user = User.objects.create_user(
        username='mgr_idc',
        email='mgr@example.test',
        password='pw',
    )
    perms = Permission.objects.filter(
        content_type__app_label='idcards',
        codename__in=['manage_idcards', 'view_idcard'],
    )
    user.user_permissions.add(*perms)
    return user


@pytest.fixture
def viewer_user(db):
    """User mit nur view_idcard, ohne manage_idcards."""
    user = User.objects.create_user(
        username='view_idc',
        email='v@example.test',
        password='pw',
    )
    perm = Permission.objects.get(
        content_type__app_label='idcards', codename='view_idcard',
    )
    user.user_permissions.add(perm)
    return user


@pytest.fixture
def department(db):
    return Department.objects.create(name='Einsatzabteilung-T', abbreviation='EA-T')


@pytest.fixture
def volunteer_unit(db):
    return VolunteerUnit.objects.create(name='Löschzug T', abbreviation='LZT')


@pytest.fixture
def person(db, admin_user, department):
    return Person.objects.create(
        first_name='Erika',
        last_name='Musterfrau',
        personnel_number='T-001',
        rank='Hauptfeuerwehrfrau',
        department=department,
        is_active=True,
        created_by=admin_user,
        updated_by=admin_user,
    )


@pytest.fixture
def person_volunteer(db, admin_user, volunteer_unit):
    return Person.objects.create(
        first_name='Hans',
        last_name='Tester',
        personnel_number='T-002',
        rank='Oberfeuerwehrmann',
        volunteer_unit=volunteer_unit,
        is_active=True,
        created_by=admin_user,
        updated_by=admin_user,
    )


@pytest.fixture
def person_incomplete(db, admin_user, department):
    """Person ohne Rang — fehlt für Templates mit {{dienstgrad}}."""
    return Person.objects.create(
        first_name='Anna',
        last_name='Unvollständig',
        personnel_number='T-003',
        rank='',  # bewusst leer
        department=department,
        is_active=True,
        created_by=admin_user,
        updated_by=admin_user,
    )


@pytest.fixture
def template_minimal(db, admin_user):
    """Minimal-Template ohne Foto, ohne Platzhalter."""
    return IdCardTemplate.objects.create(
        name='Test-Minimal',
        description='Test',
        is_portrait=False,
        front_layout=[
            {'type': 'rect', 'x': 0, 'y': 0, 'w': 85.6, 'h': 6, 'fill': '#000', 'type_color': False},
            {'type': 'text', 'x': 4, 'y': 1, 'w': 80, 'h': 4, 'value': 'AUSWEIS', 'font_size': 6, 'color': '#fff'},
        ],
        back_layout=[],
        is_system=False,
        is_default=False,
        is_active=True,
        created_by=admin_user,
        updated_by=admin_user,
    )


@pytest.fixture
def template_with_photo(db, admin_user):
    """Template mit Photo + Platzhaltern → Pre-Check fordert Felder."""
    return IdCardTemplate.objects.create(
        name='Test-Photo',
        description='Test mit Foto',
        is_portrait=False,
        front_layout=[
            {'type': 'photo', 'x': 60, 'y': 6, 'w': 22, 'h': 30, 'border_color': '#000', 'border_width': 0.4},
            {'type': 'text', 'x': 4, 'y': 6, 'w': 50, 'h': 8,
             'value': '{{vorname}} {{nachname}}', 'font_size': 9, 'color': '#000'},
            {'type': 'text', 'x': 4, 'y': 16, 'w': 50, 'h': 5,
             'value': '{{dienstgrad}}', 'font_size': 7, 'color': '#000'},
            {'type': 'text', 'x': 4, 'y': 22, 'w': 50, 'h': 5,
             'value': 'Pers.-Nr.: {{dienstnummer}}', 'font_size': 7, 'color': '#000'},
        ],
        back_layout=[
            {'type': 'text', 'x': 4, 'y': 4, 'w': 80, 'h': 5,
             'value': 'Ausweis-Nr.: {{ausweisnummer}}', 'font_size': 6, 'color': '#000'},
        ],
        is_system=False,
        is_default=True,
        is_active=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
