"""Printable invoices using ReportLab; arithmetic stays in calculations."""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from calculations import invoice_totals, line_total


def export_invoice_pdf(invoice: dict) -> bytes:
    """Return a PDF for an invoice whose numeric fields are Decimal."""
    items = invoice["items"]
    totals = invoice_totals(
        [(item["quantity"], item["unit_price"]) for item in items],
        invoice["discount_percent"],
        invoice["tax_percent"],
    )
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=42, leftMargin=42)
    styles = getSampleStyleSheet()

    def text(value, style="BodyText"):
        return Paragraph(escape(str(value)).replace("\n", "<br/>"), styles[style])

    story = [text("INVOICE", "Title"), Spacer(1, 16)]
    for label, key in [("Invoice", "invoice_number"), ("Date", "date"), ("Client", "client_name"), ("Address", "client_address")]:
        story.append(text(f"{label}: {invoice.get(key, '')}"))
    story.append(Spacer(1, 22))
    rows = [[text(value) for value in ["Description", "Quantity", "Unit price", "Amount"]]]
    for item in items:
        rows.append([
            text(item["description"]),
            text(item["quantity"]),
            text(format(item["unit_price"], ",.2f")),
            text(format(line_total(item["quantity"], item["unit_price"]), ",.2f")),
        ])
    if not items:
        rows.append([text("No line items"), "", "", ""])
    table = Table(rows, colWidths=[228, 65, 85, 150], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6edf5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey),
    ]))
    story.extend([table, Spacer(1, 20)])
    for label, key in [("Subtotal", "subtotal"), ("Discount", "discount"), ("After discount", "taxable"), ("Tax", "tax"), ("Grand total", "total")]:
        story.append(text(f"{label}: {totals[key]:,.2f}", "Heading3" if key == "total" else "BodyText"))
    story.extend([Spacer(1, 16), text("Discount is applied before tax. All amounts are in USD.")])
    document.build(story)
    return buffer.getvalue()
