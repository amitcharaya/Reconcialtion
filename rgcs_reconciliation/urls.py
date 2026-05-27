"""
URL routing for the rgcs_reconciliation application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from . import views

app_name = "rgcs_reconciliation"

urlpatterns = [
    path(
        "run/",
        views.run_rgcs_reconciliation_view,
        name="run_rgcs_reconciliation",
    ),
]