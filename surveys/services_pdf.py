"""
QR-Zettel für Umfragen mit Einmal-Links.

Erzeugt ein A4-PDF im Raster (Zettel zum Ausschneiden). Beides – WeasyPrint und
qrcode – ist bereits im Projekt vorhanden, es kommt keine neue Abhängigkeit dazu.

Muster übernommen aus `idcards/services_pdf.py` (HTML mit mm-Maßen → WeasyPrint)
und `diving/views.py` (QR-Erzeugung).
"""

import base64
import io

from django.template.loader import render_to_string


def build_qr_data_uri(url, box_size=8, border=2):
    """
    QR-Code als eingebettete PNG-Data-URI.

    Data-URI statt Datei: WeasyPrint müsste sonst auf das Dateisystem zugreifen,
    und die Zettel sind ohnehin nur für diesen einen Druck gedacht.
    """
    import qrcode

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'


#: Zettel je A4-Seite (2 Spalten x 4 Zeilen)
SLIPS_PER_PAGE = 8


def render_invitation_pdf(survey, invitations, base_url):
    """
    Baut das PDF mit einem Zettel je Einladung.

    `base_url` ist das absolute Präfix (z.B. https://lager.resqware.de) – die QR-Codes
    müssen vollständige URLs enthalten, sonst sind sie mit dem Handy nicht aufrufbar.

    Die Zettel werden hier in Seiten zu je acht gruppiert, statt den Umbruch dem
    Renderer zu überlassen: sonst beginnt am Seitenende ein angeschnittener neunter
    Zettel.
    """
    from weasyprint import HTML

    slips = [
        {
            'invitation': invitation,
            'qr': build_qr_data_uri(f"{base_url}{invitation.get_absolute_url()}"),
        }
        for invitation in invitations
    ]

    pages = [
        slips[start:start + SLIPS_PER_PAGE]
        for start in range(0, len(slips), SLIPS_PER_PAGE)
    ]

    html = render_to_string('surveys/invitation_pdf.html', {
        'survey': survey,
        'pages': pages,
    })

    buffer = io.BytesIO()
    HTML(string=html).write_pdf(buffer)
    return buffer.getvalue()
