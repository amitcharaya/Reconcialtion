"""
URL routing for the switchlog application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from .views import upload_switch_log,upload_switch_imps_file,upload_rgcs_switch_file

urlpatterns = [
    path("upload/", upload_switch_log, name="upload_switch_log"),
    path(
        "upload-imps/",
        upload_switch_imps_file,
        name="upload_switch_imps"
    ),
    path(
        "rgcs/upload/",
        upload_rgcs_switch_file,
        name="upload_rgcs_switch_file"
    ),
]