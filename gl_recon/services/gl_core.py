from decimal import Decimal
from gl_recon.models import GLDailyBalance

def get_opening_balance(gl_account, date):
    try:
        record = GLDailyBalance.objects.get(gl_account=gl_account, date=date)
        return record.opening_balance
    except GLDailyBalance.DoesNotExist:
        return Decimal("0.00")


def calculate_cbs_withdrawal_closing(opening, acq, iss):
    return opening + acq - iss

from django.db.models import Sum
from gl_recon.models import GLPending

def get_pending_totals(product, upto_date):
    data = GLPending.objects.filter(
        product=product,
        date__lte=upto_date,
        posted=False
    ).aggregate(
        approved_fee=Sum("approved_fee"),
        approved_fee_gst=Sum("approved_fee_gst"),
        switching_fee=Sum("switching_fee"),
        switching_fee_gst=Sum("switching_fee_gst")
    )

    return (
        data["approved_fee"] or Decimal("0.00"),
        data["approved_fee_gst"] or Decimal("0.00"),
        data["switching_fee"] or Decimal("0.00"),
        data["switching_fee_gst"] or Decimal("0.00")

    )

def calculate_logical_closing(cbs_closing, approved_fee, approved_fee_gst, switching_fee, switching_fee_gst):
    return cbs_closing + approved_fee +approved_fee_gst+ switching_fee + switching_fee_gst

