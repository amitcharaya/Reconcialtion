"""
Django admin configuration for the disputes application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin

from disputes.models import ATMDisputeCase, RGCSDisputeCase, IMPSDisputeCase


@admin.register(ATMDisputeCase)
class ATMDisputeCaseAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "stan_no", "rrn", "disputed_amount", "source_status", "case_status", "created_at")
    list_filter = ("transaction_date", "source_status", "case_status")
    search_fields = ("stan_no", "rrn", "account_no")


@admin.register(RGCSDisputeCase)
class RGCSDisputeCaseAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "rrn", "disputed_amount", "source_status", "case_status", "created_at")
    list_filter = ("transaction_date", "source_status", "case_status")
    search_fields = ("rrn",)


@admin.register(IMPSDisputeCase)
class IMPSDisputeCaseAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "transaction_serial_number", "rrn", "disputed_amount", "source_status", "case_status", "created_at")
    list_filter = ("transaction_date", "source_status", "case_status")
    search_fields = ("transaction_serial_number", "rrn")
