"""
Tests für die Zugriffsrechte der Organisations-Views
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from organization.models import VolunteerUnit
from permissions.constants import Roles
from permissions.management.commands.setup_verwaltungsrollen import setup_verwaltungsrollen

User = get_user_model()


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(username='plain', password='x')


@pytest.fixture
def ff_verwalter(db):
    setup_verwaltungsrollen()
    user = User.objects.create_user(username='ffverwalter', password='x')
    user.groups.add(Group.objects.get(name=Roles.FF_VERWALTER))
    return user


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse('organization:dashboard'))
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize('url_name', [
    'organization:qualification_type_create',
    'organization:supplier_create',
    'organization:volunteer_unit_create',
])
def test_create_views_forbidden_without_permission(client, plain_user, url_name):
    client.force_login(plain_user)
    assert client.get(reverse(url_name)).status_code == 403


@pytest.mark.django_db
def test_ff_verwalter_can_create_and_edit_units_but_not_delete(client, ff_verwalter):
    client.force_login(ff_verwalter)
    unit = VolunteerUnit.objects.create(name='Löschzug 1', abbreviation='LZ 1')

    assert client.get(reverse('organization:volunteer_unit_create')).status_code == 200
    assert client.get(reverse('organization:volunteer_unit_update', args=[unit.pk])).status_code == 200
    assert client.get(reverse('organization:volunteer_unit_delete', args=[unit.pk])).status_code == 403


@pytest.mark.django_db
def test_ff_verwalter_cannot_manage_other_organization_data(client, ff_verwalter):
    client.force_login(ff_verwalter)
    assert client.get(reverse('organization:department_create')).status_code == 403
    assert client.get(reverse('organization:watch_crew_create')).status_code == 403
