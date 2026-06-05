from cbs.models import CBSATMTransaction
from mis_dashboard.services.dashboard_service import MISDashboardService

from django.db.models import Max



def cbs_summary(txn_date, file_type):
    qs = CBSATMTransaction.objects.filter(
        txn_date=txn_date
    )

    debit = MISDashboardService.safe_sum(
        qs.filter(
            file_type__iexact=file_type,
            dr_cr_flag__iexact="D"
        ),
        "txn_amount"
    )

    credit = MISDashboardService.safe_sum(
        qs.filter(
            file_type__iexact=file_type,
            dr_cr_flag__iexact="C"
        ),
        "txn_amount"
    )

    return {
        "debit": debit,
        "credit": credit,
        "net": debit - credit,
    }