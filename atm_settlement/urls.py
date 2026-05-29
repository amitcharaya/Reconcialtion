from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_atm_settlement, name="upload_atm_settlement"),
    path("list/", views.atm_settlement_list, name="atm_settlement_list"),
    path("detail/<int:cycle_id>/", views.atm_settlement_detail, name="atm_settlement_detail"),
]