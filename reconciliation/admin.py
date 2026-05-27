"""
Django admin configuration for the reconciliation application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin
from .models import ATMReconciliationResult
# Register your models here.
admin.site.register(ATMReconciliationResult)