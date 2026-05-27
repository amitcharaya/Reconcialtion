"""
Django admin configuration for the cbs application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin
from .models import CBSATMTransaction,UploadBatch,CBSIMPSTransaction,CBSIMPSUploadBatch
# Register your models here.


admin.site.register(CBSIMPSTransaction)
admin.site.register(CBSIMPSUploadBatch)
@admin.register(CBSATMTransaction)
class CBSATMTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "stan_no",
        "card_no",
        'customer_account_no',
        'txn_amount',
        'status',
        'atm_id',
        'file_type',
        'dr_cr_flag',
        'txn_date'
    )
    list_filter = (
        "stan_no",
        'status',
        'atm_id'
    )
    search_fields = (
        "stan_no",
        "card_no",
        'customer_account_no',
        'txn_amount',
        'dr_cr_flag',
        'file_type',
        'txn_date'

    )
@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_date",
        "upload_status",
        "total_records",
        "total_errors",
        "uploaded_at",
    )

    list_filter = (
        "upload_status",
        "batch_date",
    )

    search_fields = (
        "batch_date",
        "acquirer_filename",
        "issuer_filename",
        "onus_filename",
    )

"""RGCS Section"""
from django.contrib import admin
from .models import RGCSUploadBatch, RGCSCBSTransaction


@admin.register(RGCSUploadBatch)
class RGCSUploadBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_date",
        "source_filename",
        "total_records",
        "total_errors",
        "upload_status",
        "uploaded_at",
    )

    list_filter = (
        "batch_date",
        "upload_status",
    )

    search_fields = (
        "source_filename",
        "remarks",
    )


@admin.register(RGCSCBSTransaction)
class RGCSCBSTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "transaction_time",
        "transaction_flag",
        "dr_cr_flag",
        "transaction_type",
        "stan_no",
        "rrn",
        "card_no",
        "transaction_amount",
        "response_code",
        "source_filename",
    )

    list_filter = (
        "transaction_date",
        "transaction_flag",
        "dr_cr_flag",
        "transaction_type",
        "response_code",
    )

    search_fields = (
        "stan_no",
        "rrn",
        "card_no",
        "account_number",
        "terminal_id",
        "source_filename",
    )