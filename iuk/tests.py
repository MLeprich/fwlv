"""Tests für das IUK-Modul (Drohnenstaffel)."""

import io
from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import User
from iuk.models import (CRITICAL_DAYS, WARNING_DAYS, Drone, DroneAccessory,
                        DroneChecklist, DroneLicense, FlightLog, LicenseState,
                        Voucher, VoucherEventType, VoucherStatus)
from iuk.services import (MODULE_GROUP, ROW_DUPLICATE, ROW_NEW, import_vouchers,
                          parse_voucher_csv, send_license_reminders)
from notifications.models import Notification


@pytest.fixture
def user(db):
    return User.objects.create_user(username='iuk-tester', password='geheim.0112')


@pytest.fixture
def iuk_user(db, user):
    """Benutzer mit allen IUK-Rechten."""
    group = Group.objects.create(name=MODULE_GROUP)
    group.permissions.add(*Permission.objects.filter(content_type__app_label='iuk'))
    user.groups.add(group)
    return user


def _license(**kwargs):
    defaults = dict(
        pilot_name='Testpilot',
        license_type='a1_a3',
        issued_date=date.today() - timedelta(days=100),
        expiry_date=date.today() + timedelta(days=365),
    )
    defaults.update(kwargs)
    return DroneLicense.objects.create(**defaults)


# ---------------------------------------------------------------- Modelle

@pytest.mark.django_db
def test_license_state_ampel():
    assert _license(expiry_date=date.today() + timedelta(days=400)).state == LicenseState.OK
    assert _license(expiry_date=date.today() + timedelta(days=WARNING_DAYS - 1)).state == LicenseState.WARNING
    assert _license(expiry_date=date.today() + timedelta(days=CRITICAL_DAYS - 1)).state == LicenseState.CRITICAL
    assert _license(expiry_date=date.today() - timedelta(days=1)).state == LicenseState.EXPIRED


@pytest.mark.django_db
def test_license_requires_person_or_name():
    license_obj = DroneLicense(
        license_type='a1_a3',
        issued_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
    )
    with pytest.raises(ValidationError):
        license_obj.full_clean()


@pytest.mark.django_db
def test_used_voucher_requires_person_and_date():
    voucher = Voucher(code='GS-1', received_date=date.today(), status=VoucherStatus.GENUTZT)
    with pytest.raises(ValidationError):
        voucher.full_clean()


@pytest.mark.django_db
def test_voucher_is_overdue():
    voucher = Voucher.objects.create(
        code='GS-2',
        received_date=date.today() - timedelta(days=30),
        valid_until=date.today() - timedelta(days=1),
    )
    assert voucher.is_overdue is True


# ---------------------------------------------------------------- Erinnerungen

@pytest.mark.django_db
def test_reminder_notifies_and_is_not_repeated(iuk_user):
    _license(expiry_date=date.today() + timedelta(days=10))

    first = send_license_reminders()
    assert first['licenses_notified'] == 1
    assert Notification.objects.filter(recipient=iuk_user).count() == 1

    # Zweiter Lauf am selben Tag darf nicht erneut erinnern
    second = send_license_reminders()
    assert second['licenses_notified'] == 0
    assert second['skipped_recent'] == 1


@pytest.mark.django_db
def test_reminder_sends_no_email(iuk_user, mailoutbox):
    """Interne Installation ohne Mailausgang: Erinnerungen bleiben in der App."""
    _license(expiry_date=date.today() + timedelta(days=10))
    result = send_license_reminders()
    assert result['notifications'] > 0
    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_reminder_ignores_licenses_far_in_the_future(iuk_user):
    _license(expiry_date=date.today() + timedelta(days=WARNING_DAYS + 30))
    result = send_license_reminders()
    assert result['checked'] == 0


# ---------------------------------------------------------------- Views

@pytest.mark.django_db
def test_dashboard_requires_permission(client, user):
    client.force_login(user)
    response = client.get(reverse('iuk:dashboard'))
    assert response.status_code == 403


@pytest.mark.django_db
def test_drone_create_via_view(client, iuk_user):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:drone_create'), {
        'designation': 'Drohne 1',
        'model': 'DJI Matrice 30T',
        'serial_number': 'SN-1',
        'lba_registration_number': 'DEuas0001',
        'status': 'einsatzbereit',
        'commissioned_date': '',
        'location': '',
        'notes': '',
        # Zubehör-Formset (wird vom Formular immer mitgeschickt)
        'accessories-TOTAL_FORMS': '0',
        'accessories-INITIAL_FORMS': '0',
        'accessories-MIN_NUM_FORMS': '0',
        'accessories-MAX_NUM_FORMS': '1000',
    })
    assert response.status_code == 302
    drone = Drone.objects.get(serial_number='SN-1')
    assert drone.created_by == iuk_user


@pytest.mark.django_db
def test_voucher_use_view_sets_status(client, iuk_user):
    voucher = Voucher.objects.create(code='GS-3', received_date=date.today())
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_use', args=[voucher.pk]), {
        'used_by': '',
        'used_by_name': 'Testpilot',
        'intended_use': 'a1_a3',
        'used_at': date.today().isoformat(),
        'license': '',
        'notes': '',
    })
    assert response.status_code == 302
    voucher.refresh_from_db()
    assert voucher.status == VoucherStatus.GENUTZT
    assert voucher.used_at == date.today()


@pytest.mark.django_db
def test_license_create_view_creates_multiple_licenses(client, iuk_user, settings, tmp_path):
    """Mehrere Nachweisarten in einem Schritt anlegen."""
    settings.MEDIA_ROOT = tmp_path
    client.force_login(iuk_user)
    today = date.today()
    response = client.post(reverse('iuk:license_create'), {
        'person': '',
        'pilot_name': 'Testpilot',
        'issuing_authority': 'Luftfahrt-Bundesamt (LBA)',
        'notes': 'Sammelanlage',
        'a1_a3_selected': 'on',
        'a1_a3_number': 'NR-1',
        'a1_a3_issued': today.isoformat(),
        'a1_a3_expiry': (today + timedelta(days=1800)).isoformat(),
        'a2_selected': 'on',
        'a2_number': 'NR-2',
        'a2_issued': today.isoformat(),
        'a2_expiry': (today + timedelta(days=1000)).isoformat(),
        'a2_document': SimpleUploadedFile('a2.pdf', b'%PDF-1.4'),
    })
    assert response.status_code == 302
    assert DroneLicense.objects.count() == 2
    a2 = DroneLicense.objects.get(license_type='a2')
    assert a2.license_number == 'NR-2'
    assert a2.created_by == iuk_user
    assert a2.document.name.endswith('.pdf')
    # Nicht ausgewählte Arten werden nicht angelegt.
    assert not DroneLicense.objects.filter(license_type='sts').exists()
    assert not DroneLicense.objects.get(license_type='a1_a3').document


@pytest.mark.django_db
def test_license_create_view_requires_a_selection(client, iuk_user):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:license_create'), {
        'pilot_name': 'Testpilot',
        'issuing_authority': 'LBA',
    })
    assert response.status_code == 200
    assert DroneLicense.objects.count() == 0
    assert 'mindestens einen Nachweis' in response.content.decode()


@pytest.mark.django_db
def test_license_create_view_requires_dates_for_selected_type(client, iuk_user):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:license_create'), {
        'pilot_name': 'Testpilot',
        'issuing_authority': 'LBA',
        'sts_selected': 'on',
    })
    assert response.status_code == 200
    assert DroneLicense.objects.count() == 0
    assert 'Pflichtfeld' in response.content.decode()


@pytest.mark.django_db
def test_license_create_view_requires_person_or_name(client, iuk_user):
    client.force_login(iuk_user)
    today = date.today()
    response = client.post(reverse('iuk:license_create'), {
        'issuing_authority': 'LBA',
        'a2_selected': 'on',
        'a2_issued': today.isoformat(),
        'a2_expiry': (today + timedelta(days=10)).isoformat(),
    })
    assert response.status_code == 200
    assert DroneLicense.objects.count() == 0
    assert 'Person ausw' in response.content.decode()


# ---------------------------------------------------------------- Gutscheine

@pytest.mark.django_db
def test_voucher_assign_view_sets_person_and_license_type(client, iuk_user):
    """Gutschein wird an eine Person für einen bestimmten Nachweis vergeben."""
    voucher = Voucher.objects.create(code='GS-10', received_date=date.today())
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_assign', args=[voucher.pk]), {
        'assigned_to': '',
        'assigned_to_name': 'Testpilot',
        'intended_use': 'a2',
        'assigned_at': date.today().isoformat(),
        'notes': '',
    })
    assert response.status_code == 302
    voucher.refresh_from_db()
    assert voucher.status == VoucherStatus.VERGEBEN
    assert voucher.assigned_to_display == 'Testpilot'
    assert voucher.intended_use == 'a2'
    assert voucher.assigned_at == date.today()


@pytest.mark.django_db
def test_voucher_assign_requires_person_and_license_type(client, iuk_user):
    voucher = Voucher.objects.create(code='GS-11', received_date=date.today())
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_assign', args=[voucher.pk]), {
        'assigned_to': '',
        'assigned_to_name': '',
        'intended_use': '',
        'assigned_at': date.today().isoformat(),
        'notes': '',
    })
    assert response.status_code == 200
    voucher.refresh_from_db()
    assert voucher.status == VoucherStatus.OFFEN


@pytest.mark.django_db
def test_voucher_use_prefills_assigned_person(client, iuk_user):
    """Nach der Vergabe ist die Person beim Einlösen bereits vorbelegt."""
    voucher = Voucher.objects.create(
        code='GS-12', received_date=date.today(),
        status=VoucherStatus.VERGEBEN, assigned_to_name='Testpilot',
        intended_use='a2', assigned_at=date.today(),
    )
    client.force_login(iuk_user)
    response = client.get(reverse('iuk:voucher_use', args=[voucher.pk]))
    assert response.status_code == 200
    assert 'Testpilot' in response.content.decode()


@pytest.mark.django_db
def test_voucher_use_requires_license_type(client, iuk_user):
    voucher = Voucher.objects.create(code='GS-13', received_date=date.today())
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_use', args=[voucher.pk]), {
        'used_by': '',
        'used_by_name': 'Testpilot',
        'intended_use': '',
        'used_at': date.today().isoformat(),
        'license': '',
        'notes': '',
    })
    assert response.status_code == 200
    voucher.refresh_from_db()
    assert voucher.status == VoucherStatus.OFFEN


@pytest.mark.django_db
def test_voucher_list_filters_by_intended_use(client, iuk_user):
    Voucher.objects.create(code='GS-A2', received_date=date.today(), intended_use='a2')
    Voucher.objects.create(code='GS-STS', received_date=date.today(), intended_use='sts')
    client.force_login(iuk_user)
    body = client.get(reverse('iuk:voucher_list'), {'intended_use': 'a2'}).content.decode()
    assert 'GS-A2' in body
    assert 'GS-STS' not in body


# ------------------------------------------------------- Gutschein-CSV-Import

def _csv_upload(text, name='gutscheine.csv'):
    return SimpleUploadedFile(name, text.encode('utf-8'), content_type='text/csv')


@pytest.mark.django_db
def test_parse_voucher_csv_with_header():
    result = parse_voucher_csv(
        'Code;Ausgegeben von;Erhalten am;Gültig bis;Für welchen Nachweis\n'
        'LBA-1;Stadt;01.03.2026;31.12.2026;A2\n'
        'LBA-2;Stadt;01.03.2026;;A1/A3\n'.encode('utf-8')
    )
    assert result['has_header'] is True
    assert result['counts'][ROW_NEW] == 2
    first = result['rows'][0]
    assert first['code'] == 'LBA-1'
    assert first['issuer'] == 'Stadt'
    assert first['received_date'] == date(2026, 3, 1)
    assert first['valid_until'] == date(2026, 12, 31)
    assert first['intended_use'] == 'a2'
    assert result['rows'][1]['intended_use'] == 'a1_a3'


@pytest.mark.django_db
def test_parse_voucher_csv_plain_code_list():
    """Reine Code-Liste ohne Kopfzeile: erste Spalte ist der Code."""
    result = parse_voucher_csv('LBA-A\nLBA-B\nLBA-C\n'.encode('utf-8'))
    assert result['has_header'] is False
    assert result['counts'][ROW_NEW] == 3
    assert [row['code'] for row in result['rows']] == ['LBA-A', 'LBA-B', 'LBA-C']


@pytest.mark.django_db
def test_parse_voucher_csv_marks_duplicates():
    Voucher.objects.create(code='LBA-1', received_date=date.today())
    result = parse_voucher_csv('Code\nLBA-1\nLBA-2\nlba-2\n\n'.encode('utf-8'))
    assert result['counts'][ROW_NEW] == 1          # nur LBA-2
    assert result['counts'][ROW_DUPLICATE] == 2    # bereits vorhanden + doppelt in der Datei
    assert result['rows'][0]['message'] == 'Code ist bereits im System vorhanden'


@pytest.mark.django_db
def test_import_vouchers_never_creates_a_code_twice(iuk_user):
    rows = parse_voucher_csv('Code\nLBA-9\n'.encode('utf-8'))['rows']
    first = import_vouchers(rows, user=iuk_user)
    assert len(first['created']) == 1
    # Dieselbe Vorschau erneut ausführen (z.B. doppelt abgeschickt)
    second = import_vouchers(rows, user=iuk_user)
    assert second['created'] == []
    assert second['skipped'] == 1
    assert Voucher.objects.filter(code='LBA-9').count() == 1


@pytest.mark.django_db
def test_voucher_import_view_two_steps(client, iuk_user):
    client.force_login(iuk_user)
    url = reverse('iuk:voucher_import')
    assert client.get(url).status_code == 200

    preview = client.post(url, {'csv_file': _csv_upload(
        'Code;Für welchen Nachweis\nLBA-100;A2\nLBA-101;A2\n')})
    assert preview.status_code == 200
    body = preview.content.decode()
    assert 'LBA-100' in body
    assert Voucher.objects.count() == 0          # noch nichts angelegt

    confirm_key = body.split('name="confirm_key" value="')[1].split('"')[0]
    done = client.post(url, {'confirm_key': confirm_key})
    assert done.status_code == 302
    assert Voucher.objects.count() == 2
    voucher = Voucher.objects.get(code='LBA-100')
    assert voucher.intended_use == 'a2'
    assert voucher.created_by == iuk_user
    assert voucher.events.filter(event_type=VoucherEventType.IMPORTIERT).exists()


@pytest.mark.django_db
def test_voucher_import_rejects_non_csv(client, iuk_user):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_import'), {
        'csv_file': SimpleUploadedFile('liste.xlsx', b'x', content_type='application/vnd.ms-excel'),
    })
    assert response.status_code == 200
    assert Voucher.objects.count() == 0
    assert 'Nur .csv' in response.content.decode() or 'CSV-Datei hochladen' in response.content.decode()


# ------------------------------------------- Einmalige Nutzung & Verlauf

@pytest.mark.django_db
def test_used_voucher_cannot_be_used_again(client, iuk_user):
    voucher = Voucher.objects.create(
        code='GS-USED', received_date=date.today(), status=VoucherStatus.GENUTZT,
        used_by_name='Testpilot', used_at=date.today(), intended_use='a2',
    )
    client.force_login(iuk_user)
    response = client.get(reverse('iuk:voucher_use', args=[voucher.pk]))
    assert response.status_code == 302
    assert response.url == reverse('iuk:voucher_detail', args=[voucher.pk])

    # Auch ein direkter POST darf den Gutschein nicht erneut verbuchen.
    response = client.post(reverse('iuk:voucher_use', args=[voucher.pk]), {
        'used_by': '', 'used_by_name': 'Jemand anderes', 'intended_use': 'sts',
        'used_at': date.today().isoformat(), 'license': '', 'notes': '',
    })
    assert response.status_code == 302
    voucher.refresh_from_db()
    assert voucher.used_by_name == 'Testpilot'
    assert voucher.intended_use == 'a2'


@pytest.mark.django_db
def test_used_voucher_cannot_be_assigned_again(client, iuk_user):
    voucher = Voucher.objects.create(
        code='GS-USED-2', received_date=date.today(), status=VoucherStatus.GENUTZT,
        used_by_name='Testpilot', used_at=date.today(), intended_use='a2',
    )
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_assign', args=[voucher.pk]), {
        'assigned_to': '', 'assigned_to_name': 'Neue Person', 'intended_use': 'sts',
        'assigned_at': date.today().isoformat(), 'notes': '',
    })
    assert response.status_code == 302
    voucher.refresh_from_db()
    assert voucher.status == VoucherStatus.GENUTZT
    assert voucher.assigned_to_name == ''


@pytest.mark.django_db
def test_voucher_history_records_who_used_it_for_what(client, iuk_user):
    """Vergabe und Einlösung landen mit Person, Nachweis und Datum im Protokoll."""
    voucher = Voucher.objects.create(code='GS-LOG', received_date=date.today())
    client.force_login(iuk_user)
    client.post(reverse('iuk:voucher_assign', args=[voucher.pk]), {
        'assigned_to': '', 'assigned_to_name': 'Testpilot', 'intended_use': 'a2',
        'assigned_at': date.today().isoformat(), 'notes': '',
    })
    client.post(reverse('iuk:voucher_use', args=[voucher.pk]), {
        'used_by': '', 'used_by_name': 'Testpilot', 'intended_use': 'a2',
        'used_at': date.today().isoformat(), 'license': '', 'notes': '',
    })
    events = list(voucher.events.order_by('created_at'))
    assert [event.event_type for event in events] == [
        VoucherEventType.VERGEBEN, VoucherEventType.GENUTZT,
    ]
    used = events[-1]
    assert used.person_display == 'Testpilot'
    assert used.license_type == 'a2'
    assert used.occurred_on == date.today()
    assert used.created_by == iuk_user

    detail = client.get(reverse('iuk:voucher_detail', args=[voucher.pk])).content.decode()
    assert 'Verlauf' in detail
    assert 'Eingelöst' in detail


@pytest.mark.django_db
def test_used_voucher_cannot_be_deleted(client, iuk_user):
    voucher = Voucher.objects.create(
        code='GS-KEEP', received_date=date.today(), status=VoucherStatus.GENUTZT,
        used_by_name='Testpilot', used_at=date.today(), intended_use='a2',
    )
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:voucher_delete', args=[voucher.pk]))
    assert response.status_code == 302
    assert Voucher.objects.filter(pk=voucher.pk).exists()


# ---------------------------------------------------------- Drohnen-Zubehör

def _drone_post_data(**overrides):
    data = {
        'designation': 'Drohne 1',
        'model': 'DJI Matrice 30T',
        'serial_number': 'SN-ZUB-1',
        'lba_registration_number': '',
        'status': 'einsatzbereit',
        'commissioned_date': '',
        'location': '',
        'notes': '',
        # Formset-Verwaltung
        'accessories-TOTAL_FORMS': '2',
        'accessories-INITIAL_FORMS': '0',
        'accessories-MIN_NUM_FORMS': '0',
        'accessories-MAX_NUM_FORMS': '1000',
    }
    data.update(overrides)
    return data


def _accessory_fields(index, **values):
    fields = {
        'category': 'sonstiges', 'name': '', 'model': '', 'quantity': '1',
        'serial_number': '', 'inventory_number': '', 'status': 'einsatzbereit',
        'commissioned_date': '', 'notes': '', 'id': '', 'DELETE': '',
    }
    fields.update(values)
    return {f'accessories-{index}-{key}': value for key, value in fields.items()}


@pytest.mark.django_db
def test_drone_create_with_accessories(client, iuk_user):
    """Zubehör wird gemeinsam mit der Drohne angelegt."""
    client.force_login(iuk_user)
    data = _drone_post_data()
    data.update(_accessory_fields(0, category='akku', name='Akku 1',
                                  model='TB30', quantity='4', serial_number='AK-1'))
    data.update(_accessory_fields(1, category='fernsteuerung', name='Smart Controller',
                                  inventory_number='INV-77'))
    response = client.post(reverse('iuk:drone_create'), data)
    assert response.status_code == 302

    drone = Drone.objects.get(serial_number='SN-ZUB-1')
    accessories = {item.name: item for item in drone.accessories.all()}
    assert set(accessories) == {'Akku 1', 'Smart Controller'}
    assert accessories['Akku 1'].quantity == 4
    assert accessories['Akku 1'].category == 'akku'
    assert accessories['Akku 1'].created_by == iuk_user
    assert accessories['Smart Controller'].inventory_number == 'INV-77'
    assert drone.accessory_total == 5


@pytest.mark.django_db
def test_drone_create_ignores_empty_accessory_rows(client, iuk_user):
    client.force_login(iuk_user)
    data = _drone_post_data()
    data.update(_accessory_fields(0, name='Koffer', category='transport'))
    data.update(_accessory_fields(1))  # komplett leere Zeile
    response = client.post(reverse('iuk:drone_create'), data)
    assert response.status_code == 302
    assert Drone.objects.get(serial_number='SN-ZUB-1').accessories.count() == 1


@pytest.mark.django_db
def test_drone_accessory_without_name_is_rejected(client, iuk_user):
    """Eine begonnene Zeile ohne Bezeichnung darf die Drohne nicht anlegen."""
    client.force_login(iuk_user)
    data = _drone_post_data()
    data.update(_accessory_fields(0, serial_number='NUR-SERIENNUMMER'))
    data.update(_accessory_fields(1))
    response = client.post(reverse('iuk:drone_create'), data)
    assert response.status_code == 200
    assert not Drone.objects.filter(serial_number='SN-ZUB-1').exists()
    assert 'Bezeichnung eintragen' in response.content.decode()


@pytest.mark.django_db
def test_drone_edit_updates_and_removes_accessories(client, iuk_user):
    drone = Drone.objects.create(designation='Drohne 2', model='M30',
                                 serial_number='SN-ZUB-2')
    keep = DroneAccessory.objects.create(drone=drone, name='Akku 1',
                                         category='akku', quantity=2)
    drop = DroneAccessory.objects.create(drone=drone, name='Alter Koffer',
                                         category='transport')
    client.force_login(iuk_user)
    data = _drone_post_data(designation='Drohne 2', serial_number='SN-ZUB-2', model='M30')
    data['accessories-TOTAL_FORMS'] = '2'
    data['accessories-INITIAL_FORMS'] = '2'
    data.update(_accessory_fields(0, name='Akku 1', category='akku',
                                  quantity='6', id=str(keep.pk)))
    data.update(_accessory_fields(1, name='Alter Koffer', category='transport',
                                  id=str(drop.pk), DELETE='on'))
    response = client.post(reverse('iuk:drone_edit', args=[drone.pk]), data)
    assert response.status_code == 302

    keep.refresh_from_db()
    assert keep.quantity == 6
    assert keep.updated_by == iuk_user
    assert not DroneAccessory.objects.filter(pk=drop.pk).exists()


@pytest.mark.django_db
def test_deleting_a_drone_removes_its_accessories(iuk_user):
    drone = Drone.objects.create(designation='Drohne 3', model='M30',
                                 serial_number='SN-ZUB-3')
    DroneAccessory.objects.create(drone=drone, name='Akku', category='akku')
    drone.delete()
    assert DroneAccessory.objects.count() == 0


# ---------------------------------------------------------------- Flugbuch

def _flight_post_data(**overrides):
    data = {
        'drone': '',
        'operation_type': 'uebung',
        'operation_number': '',
        'location': 'Feuerwache 1, Musterstadt',
        'pilot': '',
        'pilot_name': 'Testpilot',
        'camera_operator': '', 'camera_operator_name': '',
        'airspace_observer': '', 'airspace_observer_name': 'Externer Beobachter',
        'drone_lead': '', 'drone_lead_name': '',
        'overall_commander': 'BR Muster',
        'flight_date': date.today().isoformat(),
        'takeoff_time': '10:00',
        'landing_time': '10:25',
        'duration_minutes': '',
        'flight_mode': 'vlos',
        'payload': 'Wärmebildkamera',
        'description': 'Übungsflug Objektbeflug',
        'preflight_check': 'on',
        'postflight_check': 'on',
        'incident_description': '',
        'lba_report': 'nein',
    }
    data.update(overrides)
    return data


@pytest.fixture
def drone(db):
    return Drone.objects.create(designation='Drohne 1', model='M30T', serial_number='SN-FLUG')


@pytest.mark.django_db
def test_flight_create_numbers_and_calculates_duration(client, iuk_user, drone):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:flight_create'), _flight_post_data(drone=drone.pk))
    assert response.status_code == 302

    flight = FlightLog.objects.get()
    assert flight.flight_number == 1
    assert flight.year == date.today().year
    assert flight.flight_label == f'{date.today().year}-001'
    assert flight.duration_minutes == 25          # aus Start/Landung berechnet
    assert flight.pilot_display == 'Testpilot'
    assert flight.created_by == iuk_user

    # Zweiter Flug bekommt die nächste Nummer
    client.post(reverse('iuk:flight_create'),
                _flight_post_data(drone=drone.pk, takeoff_time='23:40', landing_time='00:10'))
    second = FlightLog.objects.order_by('-flight_number').first()
    assert second.flight_number == 2
    assert second.duration_minutes == 30          # über Mitternacht


@pytest.mark.django_db
def test_flight_entry_is_immutable(client, iuk_user, drone):
    client.force_login(iuk_user)
    client.post(reverse('iuk:flight_create'), _flight_post_data(drone=drone.pk))
    flight = FlightLog.objects.get()

    flight.location = 'Woanders'
    with pytest.raises(ValueError):
        flight.save()

    flight.refresh_from_db()
    assert flight.location == 'Feuerwache 1, Musterstadt'


@pytest.mark.django_db
def test_flight_requires_operation_number_for_einsatz(client, iuk_user, drone):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, operation_type='einsatz', operation_number=''))
    assert response.status_code == 200
    assert FlightLog.objects.count() == 0
    assert 'Einsatznummer' in response.content.decode()


@pytest.mark.django_db
def test_flight_requires_pilot(client, iuk_user, drone):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:flight_create'),
                           _flight_post_data(drone=drone.pk, pilot_name=''))
    assert response.status_code == 200
    assert FlightLog.objects.count() == 0
    assert 'Pilot ist ein Pflichtfeld' in response.content.decode()


@pytest.mark.django_db
def test_flight_incident_needs_description(client, iuk_user, drone):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, has_incident='on', incident_description=''))
    assert response.status_code == 200
    assert FlightLog.objects.count() == 0

    response = client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, has_incident='on',
        incident_description='Notlandung wegen Akkuwarnung', lba_report='absturz'))
    assert response.status_code == 302
    flight = FlightLog.objects.get()
    assert flight.has_incident is True
    assert flight.reported_to_lba is True


@pytest.mark.django_db
def test_flight_comment_is_added_without_changing_the_entry(client, iuk_user, drone):
    client.force_login(iuk_user)
    client.post(reverse('iuk:flight_create'), _flight_post_data(drone=drone.pk))
    flight = FlightLog.objects.get()

    response = client.post(reverse('iuk:flight_detail', args=[flight.pk]),
                           {'text': 'Nachtrag: Landung war 10:27 Uhr.'})
    assert response.status_code == 302
    comment = flight.comments.get()
    assert comment.text.startswith('Nachtrag')
    assert comment.created_by == iuk_user

    flight.refresh_from_db()
    assert flight.landing_time.strftime('%H:%M') == '10:25'   # Eintrag unverändert


@pytest.mark.django_db
def test_flight_pdfs_are_generated(client, iuk_user, drone):
    client.force_login(iuk_user)
    client.post(reverse('iuk:flight_create'), _flight_post_data(drone=drone.pk))
    flight = FlightLog.objects.get()
    flight.comments.create(text='Nachtrag zur Kontrolle', created_by=iuk_user)

    single = client.get(reverse('iuk:flight_pdf', args=[flight.pk]))
    assert single.status_code == 200
    assert single['Content-Type'] == 'application/pdf'
    assert single.content[:4] == b'%PDF'

    book = client.get(reverse('iuk:flight_book_pdf'))
    assert book.status_code == 200
    assert book.content[:4] == b'%PDF'


@pytest.mark.django_db
def test_flight_list_filters(client, iuk_user, drone):
    other = Drone.objects.create(designation='Drohne 2', model='Mini', serial_number='SN-2')
    client.force_login(iuk_user)
    client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, location='Hauptwache'))
    client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=other.pk, location='Waldgebiet Nord', operation_type='einsatz',
        operation_number='2026-4711'))

    body = client.get(reverse('iuk:flight_list'), {'operation_type': 'einsatz'}).content.decode()
    assert 'Waldgebiet Nord' in body
    assert 'Hauptwache' not in body

    body = client.get(reverse('iuk:flight_list'), {'drone': drone.pk}).content.decode()
    assert 'Hauptwache' in body
    assert 'Waldgebiet Nord' not in body


@pytest.mark.django_db
def test_flight_list_requires_permission(client, user):
    client.force_login(user)
    assert client.get(reverse('iuk:flight_list')).status_code == 403


@pytest.mark.django_db
def test_flight_without_incident_resets_lba_report(client, iuk_user, drone):
    """Ein stehengebliebener LBA-Wert blockiert das Speichern nicht."""
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, lba_report='absturz'))
    assert response.status_code == 302
    flight = FlightLog.objects.get()
    assert flight.has_incident is False
    assert flight.lba_report == 'nein'


# ------------------------------------------------- Checklisten & Flugstunden

@pytest.fixture
def preflight_checklist(db, drone):
    checklist = DroneChecklist.objects.create(
        name='Vorflug M30T',
        kind='vorflug',
        items=['Propeller prüfen', {'text': 'Luftraum geprüft', 'required': True},
               {'text': 'Sichtflugbedingungen', 'required': False}],
    )
    checklist.drones.add(drone)
    return checklist


@pytest.mark.django_db
def test_checklist_form_accepts_json_and_plain_lines(client, iuk_user, drone):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:checklist_create'), {
        'name': 'Nachflug Standard',
        'kind': 'nachflug',
        'description': '',
        'drones': [],
        'is_active': 'on',
        'items_text': '["Akkus entnehmen", {"text": "Schäden dokumentieren", "required": false}]',
    })
    assert response.status_code == 302
    checklist = DroneChecklist.objects.get(name='Nachflug Standard')
    assert checklist.normalized_items == [
        {'text': 'Akkus entnehmen', 'required': True},
        {'text': 'Schäden dokumentieren', 'required': False},
    ]

    # Zeilenweise Eingabe funktioniert ebenfalls
    response = client.post(reverse('iuk:checklist_create'), {
        'name': 'Kurzcheck', 'kind': 'vorflug', 'description': '', 'drones': [],
        'is_active': 'on', 'items_text': 'Akkustand\nWetter prüfen',
    })
    assert response.status_code == 302
    assert DroneChecklist.objects.get(name='Kurzcheck').item_count == 2


@pytest.mark.django_db
def test_checklist_form_rejects_broken_json(client, iuk_user):
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:checklist_create'), {
        'name': 'Kaputt', 'kind': 'vorflug', 'description': '', 'drones': [],
        'is_active': 'on', 'items_text': '["offen",',
    })
    assert response.status_code == 200
    assert DroneChecklist.objects.filter(name='Kaputt').count() == 0
    assert 'Ungültiges JSON' in response.content.decode()


@pytest.mark.django_db
def test_checklist_api_returns_lists_for_drone(client, iuk_user, drone, preflight_checklist):
    other_drone = Drone.objects.create(designation='Drohne X', model='Mini', serial_number='SN-X')
    allgemein = DroneChecklist.objects.create(
        name='Nachflug allgemein', kind='nachflug', items=['Akku entnehmen'])

    client.force_login(iuk_user)
    payload = client.get(reverse('iuk:drone_checklists_json'), {'drone': drone.pk}).json()
    assert [entry['name'] for entry in payload['preflight']] == ['Vorflug M30T']
    assert payload['preflight'][0]['items'][0] == {'text': 'Propeller prüfen', 'required': True}
    assert [entry['name'] for entry in payload['postflight']] == [allgemein.name]

    # Für die andere Drohne gilt nur die allgemeine Liste
    payload = client.get(reverse('iuk:drone_checklists_json'), {'drone': other_drone.pk}).json()
    assert payload['preflight'] == []


@pytest.mark.django_db
def test_flight_stores_checklist_results(client, iuk_user, drone, preflight_checklist):
    client.force_login(iuk_user)
    data = _flight_post_data(
        drone=drone.pk,
        preflight_checklist=preflight_checklist.pk,
        preflight_item_0='on',
        preflight_item_1='on',
        preflight_item_2_note='Leichter Nebel, Sicht ausreichend',
    )
    data.pop('preflight_check')          # wird durch die Checkliste gesetzt
    response = client.post(reverse('iuk:flight_create'), data)
    assert response.status_code == 302

    flight = FlightLog.objects.get()
    assert flight.preflight_checklist == preflight_checklist
    assert flight.preflight_check is True
    assert flight.preflight_results == [
        {'text': 'Propeller prüfen', 'required': True, 'ok': True, 'note': ''},
        {'text': 'Luftraum geprüft', 'required': True, 'ok': True, 'note': ''},
        {'text': 'Sichtflugbedingungen', 'required': False, 'ok': False,
         'note': 'Leichter Nebel, Sicht ausreichend'},
    ]
    assert flight.has_checklist_findings is True
    assert flight.checklist_findings[0]['phase'] == 'Vorflug'


@pytest.mark.django_db
def test_flight_requires_all_mandatory_checklist_items(client, iuk_user, drone, preflight_checklist):
    client.force_login(iuk_user)
    data = _flight_post_data(drone=drone.pk,
                             preflight_checklist=preflight_checklist.pk,
                             preflight_item_0='on')
    response = client.post(reverse('iuk:flight_create'), data)
    assert response.status_code == 200
    assert FlightLog.objects.count() == 0
    assert 'Luftraum geprüft' in response.content.decode()

    # Mit Bemerkung statt Haken lässt sich der Punkt dokumentieren
    data['preflight_item_1_note'] = 'NOTAM lag nicht vor, Start freigegeben durch Einsatzleitung'
    response = client.post(reverse('iuk:flight_create'), data)
    assert response.status_code == 302
    assert FlightLog.objects.get().preflight_results[1]['ok'] is False


@pytest.mark.django_db
def test_flight_rejects_checklist_of_other_drone(client, iuk_user, drone, preflight_checklist):
    other = Drone.objects.create(designation='Drohne Y', model='Mini', serial_number='SN-Y')
    client.force_login(iuk_user)
    response = client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=other.pk, preflight_checklist=preflight_checklist.pk, preflight_item_0='on'))
    assert response.status_code == 200
    assert FlightLog.objects.count() == 0
    assert 'nicht vorgesehen' in response.content.decode()


@pytest.mark.django_db
def test_flight_statistics_per_drone_and_pilot(client, iuk_user, drone):
    from personnel.models import Person
    person = Person.objects.create(first_name='Erika', last_name='Musterfrau',
                                   personnel_number='P-99',
                                   created_by=iuk_user, updated_by=iuk_user)
    other = Drone.objects.create(designation='Drohne 2', model='Mini', serial_number='SN-ST')
    client.force_login(iuk_user)
    # 25 min mit Person, 40 min extern auf derselben Drohne, 10 min andere Drohne
    client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, pilot=person.pk, pilot_name=''))
    client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=drone.pk, takeoff_time='12:00', landing_time='12:40'))
    client.post(reverse('iuk:flight_create'), _flight_post_data(
        drone=other.pk, takeoff_time='14:00', landing_time='14:10'))

    response = client.get(reverse('iuk:flight_statistics'))
    assert response.status_code == 200
    drone_rows, pilot_rows = [rows for _title, rows, _empty in response.context['datasets']]
    assert drone_rows[0]['name'] == 'Drohne 1'
    assert drone_rows[0]['minutes'] == 65
    assert drone_rows[0]['hours'] == '1:05 h'
    assert drone_rows[1]['minutes'] == 10

    by_name = {row['name']: row for row in pilot_rows}
    assert by_name['Testpilot']['minutes'] == 50        # 40 + 10, extern
    assert 'Erika Musterfrau' in by_name
    assert by_name['Erika Musterfrau']['minutes'] == 25

    # Filter wirkt auch auf die Auswertung
    filtered = client.get(reverse('iuk:flight_statistics'), {'drone': other.pk})
    drone_rows, _pilot_rows = [rows for _t, rows, _e in filtered.context['datasets']]
    assert len(drone_rows) == 1
    assert drone_rows[0]['minutes'] == 10


@pytest.mark.django_db
def test_flight_statistics_csv_export(client, iuk_user, drone):
    client.force_login(iuk_user)
    client.post(reverse('iuk:flight_create'), _flight_post_data(drone=drone.pk))
    response = client.get(reverse('iuk:flight_statistics_csv'))
    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    body = response.content.decode('utf-8-sig')
    assert 'Drohne;Drohne 1' in body
    assert 'Pilot;Testpilot' in body
    assert '0:25 h' in body


@pytest.mark.django_db
def test_checklist_results_appear_in_pdf(client, iuk_user, drone, preflight_checklist):
    """Die abgehakten Punkte gehören zum physischen Nachweis."""
    from pypdf import PdfReader

    client.force_login(iuk_user)
    data = _flight_post_data(
        drone=drone.pk,
        preflight_checklist=preflight_checklist.pk,
        preflight_item_0='on',
        preflight_item_1_note='NOTAM telefonisch bestätigt',
    )
    assert client.post(reverse('iuk:flight_create'), data).status_code == 302
    flight = FlightLog.objects.get()

    pdf = client.get(reverse('iuk:flight_pdf', args=[flight.pk])).content
    text = '\n'.join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
    # Überschriften erscheinen durch die Druckformatierung in Großbuchstaben
    assert 'VORFLUG M30T' in text.upper()
    assert 'Propeller prüfen' in text
    assert 'NOTAM telefonisch bestätigt' in text


@pytest.mark.django_db
def test_checklist_form_renders_drone_checkboxes(client, iuk_user, drone):
    """Die Drohnen-Auswahl darf nicht das Textfeld-Styling erben (leerer Kasten)."""
    client.force_login(iuk_user)
    html = client.get(reverse('iuk:checklist_create')).content.decode()
    assert f'<input type="checkbox" name="drones" value="{drone.pk}"' in html
    # kein Input-Styling auf den Checkboxen bzw. deren Container
    assert 'name="drones" value="%s" class="w-full px-3 py-2' % drone.pk not in html
    assert '<div id="id_drones" class="w-full' not in html
    assert drone.designation in html
    # Reihenfolge: Prüfpunkte vor der Drohnenauswahl
    assert html.index('id_items_text') < html.index('id_drones')
