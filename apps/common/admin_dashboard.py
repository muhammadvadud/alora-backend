"""Django Unfold dashboard KPI kartalari.

Bu modul view emas — UNFOLD `DASHBOARD_CALLBACK` tomonidan chaqiriladigan
oddiy funksiya. Faqat ORM yig'ma (count/sum) so'rovlarini bajaradi.
"""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.chat.models import Conversation
from apps.orders.models import Order
from apps.usage.models import UsageDaily

User = get_user_model()


def dashboard_callback(request, context):
    """KPI kartalar bilan dashboard kontekstini boyitadi."""

    day_ago = timezone.now() - timedelta(days=1)
    today = timezone.localdate()

    conversations_today = Conversation.objects.filter(created_at__gte=day_ago).count()
    orders_today = Order.objects.filter(created_at__gte=day_ago).count()
    cost_today = (
        UsageDaily.objects.filter(date=today).aggregate(total=Sum("cost_uzs"))["total"] or 0
    )

    context.update(
        {
            "kpi": [
                {
                    "title": _("Bugungi suhbatlar"),
                    "metric": str(conversations_today),
                    "subtitle": _("So'nggi 24 soat"),
                    "footer": _("Barchasi: {count} ta").format(count=Conversation.objects.count()),
                    "icon": "chat",
                },
                {
                    "title": _("Buyurtmalar"),
                    "metric": str(Order.objects.count()),
                    "subtitle": _("Bugun: {count} ta").format(count=orders_today),
                    "footer": _("Joriy buyurtmalar bazasi"),
                    "icon": "receipt_long",
                },
                {
                    "title": _("Xodimlar"),
                    "metric": str(User.objects.filter(is_staff=False).count()),
                    "subtitle": _("Admin/staff: {count} ta").format(
                        count=User.objects.filter(is_staff=True).count()
                    ),
                    "footer": _("Jamoa a'zolari"),
                    "icon": "group",
                },
                {
                    "title": _("Bugungi sarf (UZS)"),
                    "metric": f"{cost_today:,}",
                    "subtitle": str(today),
                    "footer": _("UsageDaily rollup'idan"),
                    "icon": "monitoring",
                },
            ],
            "recent_orders": [
                {
                    "number": order.number,
                    "customer": order.customer_name,
                    "status": order.get_status_display(),
                    "total": f"{order.total:,.2f} UZS",
                    "created": order.created_at.strftime("%d.%m.%Y %H:%M"),
                }
                for order in Order.objects.select_related("user").order_by("-created_at")[:6]
            ],
        }
    )
    return context
