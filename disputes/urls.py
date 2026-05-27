"""
URL routing for the disputes application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from .views import dispute_dashboard

urlpatterns = [
    path("dashboard/", dispute_dashboard, name="dispute_dashboard"),
]
