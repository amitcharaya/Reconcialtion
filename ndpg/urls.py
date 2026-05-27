"""
URL routing for the ndpg application. Each route maps a browser URL to the correct Django view.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.urls import path
from .views import upload_ndpg_files,upload_ndpg_imps_raw_view,upload_rgcs_raw_files

urlpatterns = [
    path("upload/", upload_ndpg_files, name="upload_ndpg"),
    path(
        "upload-imps-raw/",
        upload_ndpg_imps_raw_view,
        name="upload_imps_raw"
    ),
    path(
        "rgcs/upload/",
        upload_rgcs_raw_files,
        name="upload_rgcs_raw_files"
    ),
]
