"""
URL configuration for reconcilation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from mis_dashboard.views import home_page

urlpatterns = [
    path("", home_page, name="home"),
    path('admin/', admin.site.urls),
    path('', include('cbs.urls')),
    path("ndpg/", include("ndpg.urls")),
    path("switchlog/", include("switchlog.urls")),
    path("reconciliation/", include("reconciliation.urls")),
    path("disputes/", include("disputes.urls")),
    path('mis/', include('mis_dashboard.urls')),
    path("imps-reconciliation/", include("imps_reconciliation.urls")),
    path("rgcs-reconciliation/", include("rgcs_reconciliation.urls")),
    path("atm-settlement/", include("atm_settlement.urls")),
    path("gl/", include("gl_recon.urls")),
]
