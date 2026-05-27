"""
Django app configuration for the rgcs_reconciliation application.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.apps import AppConfig


class RgcsReconciliationConfig(AppConfig):
    name = 'rgcs_reconciliation'
