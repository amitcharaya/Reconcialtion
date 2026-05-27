"""
View/controller logic for the rgcs_reconciliation application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.shortcuts import render, redirect

from .forms import RGCSReconciliationForm
from .models import RGCSReconciliationResult
from .services.rgcs_reconciliation_service import run_rgcs_reconciliation
from disputes.services.dispute_service import create_rgcs_dispute_cases


def run_rgcs_reconciliation_view(request):
    summary = None
    results = None

    if request.method == "POST":
        form = RGCSReconciliationForm(request.POST)

        if form.is_valid():
            transaction_date = form.cleaned_data["transaction_date"]

            summary = run_rgcs_reconciliation(transaction_date)
            disputes_created = create_rgcs_dispute_cases(transaction_date)
            summary["disputes_created"] = disputes_created

            return redirect(
                f"/mis/rgcs-dashboard/?from_date={transaction_date}&to_date={transaction_date}"
            )

    else:
        form = RGCSReconciliationForm(initial={"transaction_date": request.GET.get("transaction_date")} if request.GET.get("transaction_date") else None)

    return render(
        request,
        "rgcs_reconciliation/run_rgcs_reconciliation.html",
        {
            "form": form,
            "summary": summary,
            "results": results,
        },
    )