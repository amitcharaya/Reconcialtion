"""
URL routing for the reconciliation application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from .views import reconcile_atm,reconciliation_dashboard,download_reconciliation_report

urlpatterns = [
    path("atm/", reconcile_atm, name="reconcile_atm"),
    path("dashboard/",reconciliation_dashboard,name="reconciliation_dashboard"),

    path(
        "download-report/",
        download_reconciliation_report,
        name="download_reconciliation_report"
    ),
]