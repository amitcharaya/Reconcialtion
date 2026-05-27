"""
Django admin configuration for the rgcs_reconciliation application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin
from .models import RGCSReconciliationResult


@admin.register(RGCSReconciliationResult)
class RGCSReconciliationResultAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "rrn",
        "cbs_amount",
        "ndpg_amount",
        "switch_amount",
        "status",
        "reconciled_at",
    )

    list_filter = (
        "transaction_date",
        "status",
    )

    search_fields = (
        "rrn",
        "status",
    )

    readonly_fields = (
        "reconciled_at",
    )