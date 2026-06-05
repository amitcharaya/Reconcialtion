from django.urls import path
from . import views

urlpatterns = [
    # Dashboard UI
    path("gl-reconciliation/", views.gl_reconciliation_view, name="gl_reconciliation"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # API Endpoint
    path("api/gl-reconciliation/", views.gl_reconciliation_api, name="gl_reconciliation_api"),
]