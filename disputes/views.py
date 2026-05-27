"""
View/controller logic for the disputes application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.shortcuts import render
from .models import ATMDisputeCase, RGCSDisputeCase, IMPSDisputeCase


def dispute_dashboard(request):
    atm_cases = ATMDisputeCase.objects.all().order_by("-created_at")
    rgcs_cases = RGCSDisputeCase.objects.all().order_by("-created_at")
    imps_cases = IMPSDisputeCase.objects.all().order_by("-created_at")

    summary = {
        "atm_total": atm_cases.count(),
        "rgcs_total": rgcs_cases.count(),
        "imps_total": imps_cases.count(),
        "total": atm_cases.count() + rgcs_cases.count() + imps_cases.count(),
        "open": (
            atm_cases.filter(case_status="OPEN").count()
            + rgcs_cases.filter(case_status="OPEN").count()
            + imps_cases.filter(case_status="OPEN").count()
        ),
        "closed": (
            atm_cases.filter(case_status="CLOSED").count()
            + rgcs_cases.filter(case_status="CLOSED").count()
            + imps_cases.filter(case_status="CLOSED").count()
        ),
    }

    return render(
        request,
        "disputes/dashboard.html",
        {
            "summary": summary,
            "atm_cases": atm_cases[:100],
            "rgcs_cases": rgcs_cases[:100],
            "imps_cases": imps_cases[:100],
            "cases": atm_cases[:100],
        }
    )
