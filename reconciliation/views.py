"""
View/controller logic for the reconciliation application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.shortcuts import render, redirect

from disputes.models import ATMDisputeCase
from .forms import ATMReconciliationForm,ReconciliationDateForm
from .engine import run_atm_reconciliation
from .models import ATMReconciliationResult
from .utils import normalize_date
import pandas as pd
from django.http import HttpResponse
from reconciliation.utils import normalize_date
from disputes.services.dispute_service import create_dispute_cases


def download_reconciliation_report(request):

    transaction_date = request.GET.get(
        "transaction_date"
    )
    print(transaction_date)
    report_type = request.GET.get(
        "report_type"
    )

    queryset = ATMReconciliationResult.objects.filter(
        transaction_date=normalize_date(transaction_date)
    )
    print(queryset)

    if report_type != "ALL":
        queryset = queryset.filter(
            status=report_type
        )

    data = list(
        queryset.values(
            "transaction_date",
            "stan_no",
            "rrn",
            "cbs_amount",
            "switch_amount",
            "ndpg_amount",
            "status",
            "matched_by",
            "remarks",
        )
    )

    df = pd.DataFrame(data)

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    )

    filename = (
        f"reconciliation_{report_type}_{transaction_date}.xlsx"
    )

    response[
        "Content-Disposition"
    ] = f'attachment; filename="{filename}"'

    df.to_excel(
        response,
        index=False,
        engine="openpyxl"
    )

    return response
def reconciliation_dashboard(request):
    form = ReconciliationDateForm()
    summary = None

    if request.method == "POST":

        form = ReconciliationDateForm(
            request.POST
        )

        if form.is_valid():

            transaction_date = form.cleaned_data[
                "transaction_date"
            ]

            run_atm_reconciliation(
                transaction_date
            )

            queryset = (
                ATMReconciliationResult.objects.filter(
                    transaction_date=transaction_date
                )
            )
            disputeset = (
                ATMDisputeCase.objects.filter(
                    transaction_date=transaction_date
                )
            )

            total = queryset.count()
            disputes_created=disputeset.count()
            matched_all = queryset.filter(
                status="MATCHED_ALL"
            ).count()

            cbs_only = queryset.filter(
                status="CBS_ONLY"
            ).count()

            switch_only = queryset.filter(
                status="SWITCH_ONLY"
            ).count()

            ndpg_only = queryset.filter(
                status="NDPG_ONLY"
            ).count()

            cbs_switch_only = queryset.filter(
                status="CBS_SWITCH_ONLY"
            ).count()

            cbs_ndpg_only = queryset.filter(
                status="CBS_NDPG_ONLY"
            ).count()

            ndpg_switch_only = queryset.filter(
                status="NDPG_SWITCH_ONLY"
            ).count()

            match_percentage = (
                round(
                    (matched_all / total) * 100,
                    2,
                )
                if total > 0 else 0
            )

            summary = {
                "disputes_created": disputes_created,
                "date": transaction_date,
                "total": total,
                "matched_all": matched_all,
                "cbs_only": cbs_only,
                "switch_only": switch_only,
                "ndpg_only": ndpg_only,
                "cbs_switch_only": cbs_switch_only,
                "cbs_ndpg_only": cbs_ndpg_only,
                "ndpg_switch_only": ndpg_switch_only,
                "match_percentage": match_percentage,
            }

    return render(
        request,
        "reconciliation/dashboard.html",
        {
            "form": form,
            "summary": summary,
        }
    )

def reconcile_atm(request):
    form = ATMReconciliationForm(initial={"transaction_date": request.GET.get("transaction_date")} if request.GET.get("transaction_date") else None)
    summary = None

    if request.method == "POST":
        form = ATMReconciliationForm(request.POST)

        if form.is_valid():
            transaction_date =normalize_date( form.cleaned_data["transaction_date"])

            run_atm_reconciliation(transaction_date)
            created_disputes = create_dispute_cases(
                transaction_date)

            results = ATMReconciliationResult.objects.filter(
                transaction_date=transaction_date
            )

            return redirect(
                f"/mis/dashboard/?from_date={transaction_date}&to_date={transaction_date}"
            )

    return render(
        request,
        "reconciliation/reconcile.html",
        {
            "form": form,
            "summary": summary,
        }
    )

