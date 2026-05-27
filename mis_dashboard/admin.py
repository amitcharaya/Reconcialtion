"""
Django admin configuration for the mis_dashboard application. Registered models can be reviewed and managed from the admin panel.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.contrib import admin

# Register your models here.
