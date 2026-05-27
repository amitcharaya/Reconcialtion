"""
Django admin configuration for the ndpg application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin

from .models import RGCSUploadBatch, RGCSRawTransaction

# Register your models here.
from django.contrib import admin
from .models import NDPGATMTransaction,NDPGUploadBatch,NDPGIMPSRawTransaction

from .models import (
    NDPGIMPSRawUploadBatch,
    NDPGIMPSRawTransaction,
)

admin.site.register(NDPGUploadBatch)

@admin.register(NDPGATMTransaction)
class NDPGATMTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "file_type",
        "cycle_no",
        "stan_no",
        "pan_number",
        "transaction_date",
        "transaction_amount",
        "response_code",
    )

    list_filter = (
        "file_type",
        "cycle_no",
        "response_code",
        "transaction_date",
    )

    search_fields = (
        "stan_no",
        "pan_number",
        "transaction_serial_number",
        "approval_number",
    )




@admin.register(NDPGIMPSRawUploadBatch)
class NDPGIMPSRawUploadBatchAdmin(admin.ModelAdmin):
    list_display = (
        "file_type",
        "file_date",
        "cycle_no",
        "source_filename",
        "total_records",
        "created_records",
        "updated_records",
        "upload_status",
        "uploaded_at",
    )

    list_filter = (
        "file_type",
        "file_date",
        "cycle_no",
        "upload_status",
    )

    search_fields = (
        "source_filename",
        "raw_header",
    )


@admin.register(NDPGIMPSRawTransaction)
class NDPGIMPSRawTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "file_type",
        "file_date",
        "cycle_no",
        "transaction_date",
        "transaction_time",
        "transaction_serial_number",
        "response_code",
        "actual_transaction_amount",
        "source_filename",
    )

    list_filter = (
        "file_type",
        "file_date",
        "cycle_no",
        "transaction_date",
        "response_code",
    )

    search_fields = (
        "transaction_serial_number",
        "pan_number",
        "approval_no",
        "source_filename",
    )


"""RGCS"""


@admin.register(RGCSUploadBatch)
class RGCSUploadBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_date",
        "record_nature",
        "total_records",
        "total_errors",
        "upload_status",
        "uploaded_at",
    )
    list_filter = ("record_nature", "upload_status", "batch_date")


@admin.register(RGCSRawTransaction)
class RGCSRawTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "transaction_time",
        "record_nature",
        "product_id",
        "transaction_type",
        "action_code",
        "response_code",
        "rrn",
        "stan_no",
        "transaction_amount",
        "source_filename",
    )
    search_fields = ("rrn", "stan_no", "pan_number", "terminal_id", "source_filename")
    list_filter = (
        "record_nature",
        "product_id",
        "action_code",
        "response_code",
        "transaction_date",
    )