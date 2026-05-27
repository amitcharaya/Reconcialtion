"""
Django admin configuration for the imps_reconciliation application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin
from .models import IMPSReconciliationResult


@admin.register(IMPSReconciliationResult)
class IMPSReconciliationResultAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "transaction_serial_number",
        "rrn",
        "cbs_amount",
        "switch_amount",
        "ndpg_amount",
        "status",
        "reconciled_at",
    )

    list_filter = (
        "transaction_date",
        "status",
    )

    search_fields = (
        "transaction_serial_number",
        "rrn",
    )