"""
View/controller logic for the imps_reconciliation application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.shortcuts import render, redirect
from django.contrib import messages
from disputes.models import IMPSDisputeCase

from switchlog.models import SwitchIMPSTransaction
from .forms import IMPSReconciliationForm
from .models import IMPSReconciliationResult
from .services import reconcile_imps_transactions
from disputes.services.dispute_service import create_imps_dispute_cases


def run_imps_reconciliation(request):
    results = None

    if request.method == "POST":
        form = IMPSReconciliationForm(request.POST)

        if form.is_valid():
            transaction_date = form.cleaned_data["transaction_date"]

            total_results = reconcile_imps_transactions(transaction_date)
            disputes_created = create_imps_dispute_cases(transaction_date)

            messages.success(
                request,
                f"IMPS reconciliation completed. Total results generated: {total_results}. Disputes created: {disputes_created}"
            )

            return redirect(
                f"/imps-reconciliation/mis-report/?from_date={transaction_date}&to_date={transaction_date}"
            )

    else:
        form = IMPSReconciliationForm(initial={"transaction_date": request.GET.get("transaction_date")} if request.GET.get("transaction_date") else None)

    return render(
        request,
        "imps_reconciliation/run_imps_reconciliation.html",
        {
            "form": form,
            "results": results,
        }
    )


def imps_mis_report(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    switch_qs = SwitchIMPSTransaction.objects.all()
    recon_qs = IMPSReconciliationResult.objects.all()
    dispute_qs = IMPSDisputeCase.objects.all()

    if from_date:
        switch_qs = switch_qs.filter(transaction_datetime__date__gte=from_date)
        recon_qs = recon_qs.filter(transaction_date__gte=from_date)
        dispute_qs = dispute_qs.filter(transaction_date__gte=from_date)

    if to_date:
        switch_qs = switch_qs.filter(transaction_datetime__date__lte=to_date)
        recon_qs = recon_qs.filter(transaction_date__lte=to_date)
        dispute_qs = dispute_qs.filter(transaction_date__lte=to_date)

    financial_switch_qs = switch_qs.filter(transaction_amount__gt=0)
    non_financial_switch_qs = switch_qs.filter(transaction_amount=0)

    success_filter = (
        Q(status__iexact="SUCCESS") |
        Q(status__iexact="SUCCESSFUL") |
        Q(status__iexact="COMPLETED") |
        Q(imps_rc="00")
    )

    failed_filter = (
        Q(status__iexact="FAILED") |
        Q(status__iexact="FAILURE") |
        Q(status__iexact="DECLINED") |
        Q(status__iexact="REJECTED")
    )

    switch_summary = {
        "total_transactions": switch_qs.count(),
        "total_amount": switch_qs.aggregate(total=Sum("transaction_amount"))["total"] or Decimal("0.00"),

        "financial_count": financial_switch_qs.count(),
        "financial_amount": financial_switch_qs.aggregate(total=Sum("transaction_amount"))["total"] or Decimal("0.00"),

        "non_financial_count": non_financial_switch_qs.count(),
        "non_financial_amount": non_financial_switch_qs.aggregate(total=Sum("transaction_amount"))["total"] or Decimal("0.00"),

        "successful_financial_count": financial_switch_qs.filter(success_filter).count(),
        "successful_financial_amount": financial_switch_qs.filter(success_filter).aggregate(
            total=Sum("transaction_amount")
        )["total"] or Decimal("0.00"),

        "failed_financial_count": financial_switch_qs.filter(failed_filter).count(),
        "failed_financial_amount": financial_switch_qs.filter(failed_filter).aggregate(
            total=Sum("transaction_amount")
        )["total"] or Decimal("0.00"),

        "successful_non_financial_count": non_financial_switch_qs.filter(success_filter).count(),
        "failed_non_financial_count": non_financial_switch_qs.filter(failed_filter).count(),
    }

    matched_statuses = [
        "MATCHED_ALL",
    ]

    unmatched_statuses = [
        "CBS_ONLY",
        "SWITCH_ONLY",
        "NDPG_ONLY",
        "CBS_SWITCH_ONLY",
        "CBS_NDPG_ONLY",
        "SWITCH_NDPG_ONLY",
        "AMOUNT_MISMATCH",
        "FAILED_NDPG_ONLY",
    ]

    no_dispute_statuses = [
        "CBS_AUTO_REVERSED",
    ]

    reconciliation_summary = {
        "total_reconciliation_records": recon_qs.count(),

        "matched_count": recon_qs.filter(status__in=matched_statuses).count(),
        "matched_amount": recon_qs.filter(status__in=matched_statuses).aggregate(
            total=Sum("cbs_amount")
        )["total"] or Decimal("0.00"),

        "unmatched_count": recon_qs.filter(status__in=unmatched_statuses).count(),
        "unmatched_amount": recon_qs.filter(status__in=unmatched_statuses).aggregate(
            total=Sum("cbs_amount")
        )["total"] or Decimal("0.00"),

        "no_dispute_count": recon_qs.filter(status__in=no_dispute_statuses).count(),

        "amount_mismatch_count": recon_qs.filter(status="AMOUNT_MISMATCH").count(),
        "cbs_only_count": recon_qs.filter(status="CBS_ONLY").count(),
        "switch_only_count": recon_qs.filter(status="SWITCH_ONLY").count(),
        "ndpg_only_count": recon_qs.filter(status="NDPG_ONLY").count(),
        "cbs_switch_only_count": recon_qs.filter(status="CBS_SWITCH_ONLY").count(),
        "cbs_ndpg_only_count": recon_qs.filter(status="CBS_NDPG_ONLY").count(),
        "switch_ndpg_only_count": recon_qs.filter(status="SWITCH_NDPG_ONLY").count(),
        "failed_ndpg_only_count": recon_qs.filter(status="FAILED_NDPG_ONLY").count(),
        "cbs_auto_reversed_count": recon_qs.filter(status="CBS_AUTO_REVERSED").count(),
    }

    dispute_summary = {
        "total_disputes": dispute_qs.count(),
        "open_disputes": dispute_qs.filter(case_status="OPEN").count(),
        "financial_exposure": dispute_qs.filter(case_status="OPEN").aggregate(
            total=Sum("disputed_amount")
        )["total"] or Decimal("0.00"),
    }

    dispute_status_summary = dispute_qs.values("case_status").annotate(
        total_count=Count("id"),
        total_amount=Sum("disputed_amount"),
    ).order_by("case_status")

    recent_disputes = dispute_qs.order_by("-created_at")[:10]

    status_wise_summary = recon_qs.values("status").annotate(
        total_count=Count("id"),
        cbs_total=Sum("cbs_amount"),
        switch_total=Sum("switch_amount"),
        ndpg_total=Sum("ndpg_amount"),
    ).order_by("status")

    return render(
        request,
        "imps_reconciliation/imps_mis_report.html",
        {
            "from_date": from_date,
            "to_date": to_date,
            "switch_summary": switch_summary,
            "reconciliation_summary": reconciliation_summary,
            "status_wise_summary": status_wise_summary,
            "dispute_summary": dispute_summary,
            "dispute_status_summary": dispute_status_summary,
            "recent_disputes": recent_disputes,
        }
    )