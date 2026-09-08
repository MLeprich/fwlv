"""
Richtet die drei getrennten Verwaltungsrollen ein (idempotent, additiv für
bestehende Gruppen). Kann gefahrlos auf Produktion laufen, weil andere
Gruppen nicht angefasst werden:

- Personalverwalter   -> alle personnel.*-Rechte, KEINE Benutzer-/System-Rechte
- FF Verwalter        -> FF-Verwaltung über alle Einheiten (+ Dienstgrade)
- Benutzerverwalter   -> Benutzerkonten und Rollen (core.manage_users, core.assign_roles)

Außerdem bekommen FF Einheitsführer / FF Vertreter / Administrator das neue
Recht personnel.manage_ff_person, über das die FF-Verwaltung freigeschaltet wird.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from permissions.constants import Roles


# Rechte, die die FF-Verwaltung für die eigene Einheit braucht (bestehend)
FF_LEADER_CODENAMES = [
    'manage_ff_person',
    'view_qualification', 'add_qualification', 'change_qualification',
    'view_dutyhoursentry', 'add_dutyhoursentry', 'change_dutyhoursentry',
    'view_rank', 'view_personrank',
]

# FF Verwalter: zusätzlich Dienstgrade pflegen
FF_VERWALTER_CODENAMES = FF_LEADER_CODENAMES + [
    'add_rank', 'change_rank', 'delete_rank',
    'add_personrank', 'change_personrank', 'delete_personrank',
]

BENUTZERVERWALTER_PERMS = [
    ('core', 'view_user'), ('core', 'add_user'), ('core', 'change_user'),
    ('core', 'manage_users'), ('core', 'assign_roles'),
    ('auth', 'view_group'),
]


def _perms(app_label, codenames):
    return list(Permission.objects.filter(content_type__app_label=app_label, codename__in=codenames))


def setup_verwaltungsrollen(out=None):
    """Kernlogik, wird auch von setup_permissions aufgerufen."""
    log = out or (lambda msg: None)

    with transaction.atomic():
        manage_ff = _perms('personnel', ['manage_ff_person'])

        # 1. Personalverwalter: nur Personalakten
        group, created = Group.objects.get_or_create(name=Roles.PERSONALVERWALTER)
        personnel_perms = Permission.objects.filter(
            content_type__app_label='personnel'
        ).exclude(codename='manage_ff_person')
        group.permissions.set(personnel_perms)
        log(f'  ✓ {Roles.PERSONALVERWALTER}: {"erstellt" if created else "bereinigt"} '
            f'({personnel_perms.count()} Rechte, keine core.*/auth.*)')

        # 2. FF Verwalter: alle Einheiten
        group, created = Group.objects.get_or_create(name=Roles.FF_VERWALTER)
        ff_perms = _perms('personnel', FF_VERWALTER_CODENAMES)
        group.permissions.set(ff_perms)
        log(f'  ✓ {Roles.FF_VERWALTER}: {"erstellt" if created else "aktualisiert"} ({len(ff_perms)} Rechte)')

        # 3. Benutzerverwalter
        group, created = Group.objects.get_or_create(name=Roles.BENUTZERVERWALTER)
        user_perms = [p for app, code in BENUTZERVERWALTER_PERMS for p in _perms(app, [code])]
        group.permissions.set(user_perms)
        log(f'  ✓ {Roles.BENUTZERVERWALTER}: {"erstellt" if created else "aktualisiert"} ({len(user_perms)} Rechte)')

        # 4. manage_ff_person additiv an bestehende FF-Rollen und Administrator
        for role_name in [Roles.FF_EINHEITSFUEHRER, Roles.FF_VERTRETER, Roles.ADMINISTRATOR]:
            group, _ = Group.objects.get_or_create(name=role_name)
            group.permissions.add(*manage_ff)
            log(f'  ✓ {role_name}: personnel.manage_ff_person ergänzt')


class Command(BaseCommand):
    help = 'Richtet Personalverwalter, FF Verwalter und Benutzerverwalter ein (idempotent)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Verwaltungsrollen ==='))
        setup_verwaltungsrollen(out=lambda msg: self.stdout.write(self.style.SUCCESS(msg)))
        self.stdout.write(self.style.SUCCESS('✓ Verwaltungsrollen eingerichtet'))
