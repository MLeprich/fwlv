"""
Custom Middleware für FLVS
"""

from django.shortcuts import redirect
from django.urls import reverse


class QRCodeScannerMiddleware:
    """
    Middleware für QR-Code/Barcode Scanner

    Erkennt URLs im 'q' Parameter und leitet automatisch weiter.
    Funktioniert auf allen Seiten der Anwendung.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Prüfe ob ein QR-Code/Barcode gescannt wurde
        scanned_value = request.GET.get('q', '').strip()

        if scanned_value and scanned_value.startswith('/'):
            # Der gescannte Wert ist eine URL - direkt weiterleiten
            return redirect(scanned_value)

        response = self.get_response(request)
        return response


class PasswordChangeRequiredMiddleware:
    """
    Middleware zum Erzwingen einer Passwortänderung

    Wenn ein Benutzer das Flag 'password_must_change' gesetzt hat,
    wird er zur Passwortänderung weitergeleitet.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pfade, die auch mit password_must_change erlaubt sind
        allowed_paths = [
            reverse('core:force_password_change'),
            reverse('core:logout'),
            '/static/',
            '/media/',
        ]

        # Prüfen ob Benutzer eingeloggt ist und Passwort ändern muss
        if (request.user.is_authenticated and
            hasattr(request.user, 'password_must_change') and
            request.user.password_must_change):

            # Prüfen ob aktueller Pfad erlaubt ist
            current_path = request.path
            if not any(current_path.startswith(path) for path in allowed_paths):
                return redirect('core:force_password_change')

        response = self.get_response(request)
        return response



class ContentSecurityPolicyMiddleware:
    """
    CSP Middleware für FLVS
    Erlaubt Tailwind CDN und andere externe Ressourcen
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # CSP Header setzen
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "img-src 'self' data: blob: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'self'",
        ]

        response['Content-Security-Policy'] = '; '.join(csp_directives)

        return response
