"""
Django admin configuration for the switchlog application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin
from .models import *

admin.site.register(SwitchLogUploadBatch)
admin.site.register(SwitchIMPSUploadBatch)
admin.site.register(SwitchIMPSTransaction)
@admin.register(SwitchATMTransaction)

class SwitchATMTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "rrn",
        "stan_no",
        "terminal_id",
        "transaction_amount",
        "void_code",
        "transaction_status",
    )

    list_filter = (
        "transaction_date",
        "void_code",
        "transaction_status",
    )

    search_fields = (
        "rrn",
        "stan_no",
        "card_no",
        "terminal_id",
    )

from django.contrib import admin
from .models import RGCSSwitchUploadBatch, RGCSSwitchTransaction


@admin.register(RGCSSwitchUploadBatch)
class RGCSSwitchUploadBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_date",
        "source_filename",
        "total_records",
        "total_errors",
        "upload_status",
        "uploaded_at",
    )
    search_fields = ("source_filename",)
    list_filter = ("upload_status", "batch_date")


@admin.register(RGCSSwitchTransaction)
class RGCSSwitchTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "tranx_date",
        "tranx_time",
        "terminal_type",
        "stan_no",
        "rrn",
        "txn_type",
        "amount_req",
        "amount_approved",
        "interface_type",
        "void_code",
        "status",
    )
    search_fields = (
        "stan_no",
        "rrn",
        "card_no",
        "account_no",
        "terminal_id",
        "source_filename",
    )
    list_filter = (
        "tranx_date",
        "terminal_type",
        "interface_type",
        "void_code",
        "status",
    )