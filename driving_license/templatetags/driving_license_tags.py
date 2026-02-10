"""
Template tags for driving license module
"""
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.filter
def get_expiry_warnings(check, days_threshold=30):
    """
    Returns a list of expiry warnings for a DrivingLicenseCheck.
    Each warning contains: label, date, status ('expired' or 'expiring'), days_left
    """
    warnings = []
    today = timezone.now().date()
    threshold_date = today + timedelta(days=days_threshold)

    # Führerschein-Dokument
    if check.license_expiry_date:
        if check.license_expiry_date < today:
            warnings.append({
                'label': 'FS-Dokument',
                'date': check.license_expiry_date,
                'status': 'expired',
                'days_left': 0
            })
        elif check.license_expiry_date <= threshold_date:
            days_left = (check.license_expiry_date - today).days
            warnings.append({
                'label': 'FS-Dokument',
                'date': check.license_expiry_date,
                'status': 'expiring',
                'days_left': days_left
            })

    # Klasse C/C1
    if check.has_class_C or check.has_class_C1:
        if check.class_c_expiry_date:
            if check.class_c_expiry_date < today:
                warnings.append({
                    'label': 'C/C1',
                    'date': check.class_c_expiry_date,
                    'status': 'expired',
                    'days_left': 0
                })
            elif check.class_c_expiry_date <= threshold_date:
                days_left = (check.class_c_expiry_date - today).days
                warnings.append({
                    'label': 'C/C1',
                    'date': check.class_c_expiry_date,
                    'status': 'expiring',
                    'days_left': days_left
                })

    # Klasse CE/C1E
    if check.has_class_CE or check.has_class_C1E:
        if check.class_ce_expiry_date:
            if check.class_ce_expiry_date < today:
                warnings.append({
                    'label': 'CE/C1E',
                    'date': check.class_ce_expiry_date,
                    'status': 'expired',
                    'days_left': 0
                })
            elif check.class_ce_expiry_date <= threshold_date:
                days_left = (check.class_ce_expiry_date - today).days
                warnings.append({
                    'label': 'CE/C1E',
                    'date': check.class_ce_expiry_date,
                    'status': 'expiring',
                    'days_left': days_left
                })

    # Klasse D
    if check.has_class_D:
        if check.class_d_expiry_date:
            if check.class_d_expiry_date < today:
                warnings.append({
                    'label': 'D',
                    'date': check.class_d_expiry_date,
                    'status': 'expired',
                    'days_left': 0
                })
            elif check.class_d_expiry_date <= threshold_date:
                days_left = (check.class_d_expiry_date - today).days
                warnings.append({
                    'label': 'D',
                    'date': check.class_d_expiry_date,
                    'status': 'expiring',
                    'days_left': days_left
                })

    return warnings
