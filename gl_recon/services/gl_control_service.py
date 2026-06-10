from gl_recon.models import GLOpeningBalance,GLAccount
from django.db.models import Sum
from decimal import Decimal
from datetime import date

from gl_recon.models import GLDailyBalance
from cbs.models import CBSATMTransaction


def get_opening_balance(gl_account, txn_date):

    prev_entry = GLDailyBalance.objects.filter(
        gl_account=gl_account,
        balance_date__lt=txn_date
    ).order_by("-balance_date").first()

    if prev_entry:
        return prev_entry.closing_balance

    # fallback to GL master
    opening_balance=GLOpeningBalance.objects.filter(gl_account=gl_account).first()
    return opening_balance.opening_balance


from decimal import Decimal
from django.db import transaction

def update_gl_balances(txn_date,acquirer,issuer,gl):


    with transaction.atomic():

        # -------------------------------
        # ACQUIRER
        # -------------------------------
        gl = gl

        opening = get_opening_balance(gl, txn_date)

        obj, _ = GLDailyBalance.objects.get_or_create(
            gl_account=gl,
            balance_date=txn_date,
            defaults={"opening_balance": opening}
        )

        obj.opening_balance = opening
        obj.debit_during_the_day = acquirer["debit"]
        obj.credit_during_the_day= acquirer["credit"]
        obj.txn_type="ACQUIRER"
        obj.save()
        print(obj)
        opening = opening + acquirer["net"]
        obj = GLDailyBalance.objects.create(
            gl_account=gl,
            balance_date=txn_date,
           opening_balance= opening
        )


        obj.opening_balance = opening
        obj.debit_during_the_day =  issuer["credit"]
        obj.credit_during_the_day = issuer["debit"]
        obj.txn_type = "ISSUER"
        obj.save()
        print(obj)


def validate_gl_mapping(product, txn_type, date, request):

    gl = GLAccount.objects.filter(
        product=product,
        gl_type=txn_type,
        is_active=True
    ).first()

    current_url = request.get_full_path()

    if not gl:
        return {
            "status": False,
            "redirect": f"/gl/create/?next={current_url}"
        }

    opening = GLOpeningBalance.objects.filter(
        gl_account=gl,
        opening_date__lte=date
    ).order_by("-opening_date").first()

    if not opening:
        return {
            "status": False,
            "redirect": f"/gl/opening/?gl_id={gl.id}&next={current_url}"
        }

    return {"status": True, "gl": gl}






def update_gl_daily_balance(txn_date, gl_code):
    # Aggregate totals
    acquirer_total = CBSATMTransaction.objects.filter(
        transaction_date=txn_date,
        file_type="A"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    issuer_total = CBSATMTransaction.objects.filter(
        transaction_date=txn_date,
        txn_type="ISSUER"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Get previous closing balance
    prev_balance = GLDailyBalance.objects.filter(
        gl_account=gl_code,
        balance_date__lt=txn_date
    ).order_by("-balance_date").first()

    opening_balance = prev_balance.closing_balance if prev_balance else Decimal("0.00")

    # Create or update GL entry
    obj, created = GLDailyBalance.objects.update_or_create(
        gl_account=gl_code,
        balance_date=txn_date,
        defaults={
            "opening_balance": opening_balance,
            "debit_during_the_day": acquirer_total,
            "credit_during_the_day": issuer_total,
        }
    )

    return obj