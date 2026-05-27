"""
URL routing for the cbs application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from .views import upload_cbs_files,upload_cbs_imps_files,upload_rgcs_cbs_file

urlpatterns = [
    path("upload/", upload_cbs_files, name="upload_cbs"),
    path("upload-imps/",upload_cbs_imps_files, name="upload_cbs_imps" ),
    path(
        "upload-rgcs-cbs/",
        upload_rgcs_cbs_file,
        name="upload_rgcs_cbs_file"
    ),
]
