"""Kommercheskiy taklif PDF generatsiyasi (8.15).

Toza interfeys: `generate_order_pdf(order)` — PDF baytlarini qaytaradi.
Kutubxona (reportlab / weasyprint) o'rnatilmagan bo'lsa `PdfUnavailableError`
chiqariladi, view uni 503 holatiga o'giradi.
"""

from __future__ import annotations

from django.utils import timezone

from apps.orders.models import Order


class PdfUnavailableError(RuntimeError):
    """PDF kutubxonasi mavjud emasligi haqidagi xato."""


UNAVAILABLE_MESSAGE = (
    "Kommercheskiy taklif PDF faylini tayyorlash uchun 'reportlab' yoki 'weasyprint' "
    "kutubxonasi o'rnatilishi kerak. Iltimos, administrator bilan bog'laning."
)


def _load_pdf_library() -> str | None:
    """Mavjud PDF kutubxonasi nomini qaytaradi (aks holda None)."""

    try:
        import reportlab  # noqa: F401

        return "reportlab"
    except ImportError:
        pass
    try:
        import weasyprint  # noqa: F401

        return "weasyprint"
    except ImportError:
        return None


def generate_order_pdf(*, order: Order) -> bytes:
    """Berilgan buyurtma uchun kommercheskiy taklif PDF'ini qaytaradi.

    Kutubxona mavjud bo'lmasa `PdfUnavailableError` chiqariladi.
    """

    library = _load_pdf_library()
    if library is None:
        raise PdfUnavailableError(UNAVAILABLE_MESSAGE)
    if library == "reportlab":
        return _render_with_reportlab(order)
    return _render_with_weasyprint(order)


def _render_with_reportlab(order: Order) -> bytes:
    """reportlab yordamida oddiy taklif hujjatini tayyorlaydi."""

    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Kommercheskiy taklif № {order.number}", styles["Title"]),
        Spacer(1, 4 * mm),
        Paragraph(f"Mijoz: {order.customer_name} ({order.customer_phone})", styles["Normal"]),
        Paragraph(f"Mijoz sanasi: {timezone.localdate().isoformat()}", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    rows = [["Mahsulot / xizmat", "Miqdor", "Birlik", "Narx", "Summa"]]
    for measurement in order.measurements.all():
        for part in measurement.parts.all():
            rows.append(
                [
                    f"{measurement.room_name} — {part.variant.sku}",
                    str(part.area_sqm),
                    "m²",
                    str(part.price_per_sqm),
                    str(part.total),
                ]
            )
        for accessory in measurement.accessories.all():
            rows.append(
                [
                    accessory.variant.sku,
                    str(accessory.qty),
                    accessory.unit,
                    str(accessory.unit_price),
                    str(accessory.total),
                ]
            )
    for item in order.items.all():
        rows.append(
            [item.name_snapshot, str(item.qty), item.unit, str(item.unit_price), str(item.total)]
        )

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            (f"Jami: {order.total} so'm<br/>Avans: {order.prepayment} so'm<br/>"
             f"Qoldiq: {order.balance} so'm"),
            styles["Normal"],
        )
    )
    document.build(story)
    return buffer.getvalue()


def _render_with_weasyprint(order: Order) -> bytes:
    """weasyprint yordamida HTML asosidagi taklif hujjatini tayyorlaydi."""

    import weasyprint

    html = _order_html(order)
    return weasyprint.HTML(string=html, encoding="utf-8").write_pdf()


def _order_html(order: Order) -> str:
    """Buyurtma uchun oddiy, xavfsiz HTML hujjat quradi."""

    from django.utils.html import escape

    lines = [
        f"<h1>Kommercheskiy taklif № {escape(order.number)}</h1>",
        f"<p>Mijoz: {escape(order.customer_name)} ({escape(order.customer_phone)})</p>",
        f"<p>Sana: {timezone.localdate().isoformat()}</p>",
        "<table border='1' cellpadding='4' style='border-collapse: collapse; width: 100%'>",
        "<tr><th>Mahsulot / xizmat</th><th>Miqdor</th><th>Birlik</th><th>Narx</th><th>Summa</th></tr>",
    ]
    for measurement in order.measurements.all():
        for part in measurement.parts.all():
            lines.append(
                f"<tr><td>{escape(measurement.room_name)} — {escape(part.variant.sku)}</td>"
                f"<td>{part.area_sqm}</td><td>m²</td><td>{part.price_per_sqm}</td><td>{part.total}</td></tr>"
            )
        for accessory in measurement.accessories.all():
            lines.append(
                f"<tr><td>{escape(accessory.variant.sku)}</td><td>{accessory.qty}</td>"
                f"<td>{accessory.unit}</td><td>{accessory.unit_price}</td><td>{accessory.total}</td></tr>"
            )
    for item in order.items.all():
        lines.append(
            f"<tr><td>{escape(item.name_snapshot)}</td><td>{item.qty}</td><td>{item.unit}</td>"
            f"<td>{item.unit_price}</td><td>{item.total}</td></tr>"
        )
    lines.append("</table>")
    lines.append(
        f"<p>Jami: {order.total} so'm · Avans: {order.prepayment} so'm · "
        f"Qoldiq: {order.balance} so'm</p>"
    )
    return "\n".join(lines)