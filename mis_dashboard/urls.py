"""
URL routing for the mis_dashboard application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from . import views

app_name = "mis_dashboard"

urlpatterns = [
    path("home/", views.home_page, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    path(
        "reconciliation-report/",
        views.reconciliation_report_view,
        name="reconciliation_report"
    ),

    path(
        "dispute-report/",
        views.dispute_report_view,
        name="dispute_report"
    ),

    path(
        "download-reconciliation-excel/",
        views.download_reconciliation_excel,
        name="download_reconciliation_excel"
    ),

    path(
        "download-dispute-excel/",
        views.download_dispute_excel,
        name="download_dispute_excel"
    ),
    path(
        "",
        views.upload_monitoring_view,
        name="upload_monitoring"
    ),
path(
    "rgcs-dashboard/",
    views.rgcs_dashboard_view,
    name="rgcs_dashboard"
),

path(
    "rgcs-reconciliation-report/",
    views.rgcs_reconciliation_report_view,
    name="rgcs_reconciliation_report"
),

path(
    "download-rgcs-reconciliation-excel/",
    views.download_rgcs_reconciliation_excel,
    name="download_rgcs_reconciliation_excel"
),
]