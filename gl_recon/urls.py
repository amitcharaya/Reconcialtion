from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_gl, name="create_gl"),
    path("opening/", views.set_opening_balance, name="set_opening_balance"),
]