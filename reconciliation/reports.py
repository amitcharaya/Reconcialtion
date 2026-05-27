"""
Python module used by the reconciliation application.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

import pandas as pd

def download_reconciliation_report(request):

    transaction_date = request.GET.get(
        "transaction_date"
    )

    report_type = request.GET.get(
        "report_type"
    )

    queryset = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date
    )

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