import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def generate_pdf_certificate(
    output_path: str,
    recipient_name: str,
    event_name: str,
    organization_name: str,
    issue_date: str,
    certificate_id: str,
) -> None:
    """Generates a professional landscape PDF certificate using ReportLab canvas.

    Args:
        output_path: Destination file path for generated PDF.
        recipient_name: Full name of recipient.
        event_name: Title of event/course.
        organization_name: Name of issuing organization.
        issue_date: Issue date string.
        certificate_id: Unique certificate ID string.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    width, height = landscape(letter)

    c = canvas.Canvas(output_path, pagesize=landscape(letter))
    c.setTitle(f"Certificate - {certificate_id}")

    # Color palette
    primary_color = colors.HexColor("#1A365D")    # Deep Navy Blue
    secondary_color = colors.HexColor("#D69E2E")  # Gold / Amber Accent
    text_dark = colors.HexColor("#2D3748")        # Dark Charcoal
    accent_gray = colors.HexColor("#718096")      # Slate Gray

    # Outer decorative border
    margin = 25
    c.setLineWidth(4)
    c.setStrokeColor(primary_color)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Inner gold border
    inner_margin = 33
    c.setLineWidth(1.5)
    c.setStrokeColor(secondary_color)
    c.rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin)

    # Corner square accents
    corner_size = 10
    c.setFillColor(secondary_color)
    c.rect(inner_margin - 2, inner_margin - 2, corner_size, corner_size, fill=1, stroke=0)
    c.rect(width - inner_margin - corner_size + 2, inner_margin - 2, corner_size, corner_size, fill=1, stroke=0)
    c.rect(inner_margin - 2, height - inner_margin - corner_size + 2, corner_size, corner_size, fill=1, stroke=0)
    c.rect(width - inner_margin - corner_size + 2, height - inner_margin - corner_size + 2, corner_size, corner_size, fill=1, stroke=0)

    # Header: Organization Name
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(primary_color)
    c.drawCentredString(width / 2.0, height - 85, organization_name.upper())

    # Gold dividing line below Organization Name
    c.setLineWidth(1)
    c.setStrokeColor(secondary_color)
    c.line(width / 2.0 - 160, height - 98, width / 2.0 + 160, height - 98)

    # Main Title
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(primary_color)
    c.drawCentredString(width / 2.0, height - 150, "CERTIFICATE OF COMPLETION")

    # Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(accent_gray)
    c.drawCentredString(width / 2.0, height - 190, "PROUDLY PRESENTED TO")

    # Recipient Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(text_dark)
    c.drawCentredString(width / 2.0, height - 235, recipient_name)

    # Underline for recipient name
    c.setLineWidth(1)
    c.setStrokeColor(primary_color)
    c.line(width / 2.0 - 200, height - 245, width / 2.0 + 200, height - 245)

    # Completion statement
    c.setFont("Helvetica", 14)
    c.setFillColor(accent_gray)
    c.drawCentredString(width / 2.0, height - 280, "for successfully participating in and completing")

    # Event Name
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(primary_color)
    c.drawCentredString(width / 2.0, height - 315, event_name)

    # Left Footer: Issue Date
    c.setFont("Helvetica", 11)
    c.setFillColor(text_dark)
    c.drawString(70, 80, f"Date of Issue: {issue_date}")
    c.setLineWidth(0.5)
    c.setStrokeColor(accent_gray)
    c.line(70, 75, 230, 75)

    # Right Footer: Certificate ID
    c.drawRightString(width - 70, 80, f"Certificate ID: {certificate_id}")
    c.line(width - 230, 75, width - 70, 75)

    # Center Footer: Gold Verification Seal
    c.setFillColor(secondary_color)
    c.circle(width / 2.0, 80, 22, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.white)
    c.drawCentredString(width / 2.0, 77, "VERIFIED")

    c.showPage()
    c.save()
