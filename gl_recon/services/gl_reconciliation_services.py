from decimal import Decimal
from django.db.models import Sum

from atm_settlement.models import ATMSettlementCycle, ATMSettlementItem
from gl_recon.models import GLDailyBalance


def run_gl_reconciliation(settlement_date):
    """
    End-to-End GL Reconciliation for a given date
    """

    # -------------------------------
    # 1. FETCH NTSL DATA
    # -------------------------------
    cycles = ATMSettlementCycle.objects.filter(settlement_date=settlement_date)

    acquirer_amt = ATMSettlementItem.objects.filter(
        settlement_cycle__in=cycles,
        description__icontains="Acquirer WDL Transaction Amount"
    ).aggregate(total=Sum("credit_amount"))["total"] or Decimal("0.00")

    issuer_amt = ATMSettlementItem.objects.filter(
        settlement_cycle__in=cycles,
        description__icontains="Issuer WDL Transaction Amount"
    ).aggregate(total=Sum("debit_amount"))["total"] or Decimal("0.00")

    final_settlement = cycles.aggregate(
        total=Sum("final_settlement_amount")
    )["total"] or Decimal("0.00")

    # -------------------------------
    # 2. FETCH GL BALANCES
    # -------------------------------
    withdrawal_gl = GLDailyBalance.objects.filter(
        gl_account="ATM_WITHDRAWAL",
        balance_date=settlement_date
    ).first()

    settlement_gl = GLDailyBalance.objects.filter(
        gl_account="ATM_SETTLEMENT",
        balance_date=settlement_date
    ).first()

    if not withdrawal_gl or not settlement_gl:
        raise Exception("GL balances not found for date")

    # -------------------------------
    # 3. COMPUTE EXPECTED VALUES
    # -------------------------------
    expected_withdrawal_closing = (
        withdrawal_gl.opening_balance
        + acquirer_amt
        - issuer_amt
    )

    expected_settlement_closing = (
        settlement_gl.opening_balance
        + final_settlement
    )

    # -------------------------------
    # 4. COMPARE WITH ACTUAL
    # -------------------------------
    withdrawal_diff = expected_withdrawal_closing - withdrawal_gl.closing_balance
    settlement_diff = expected_settlement_closing - settlement_gl.closing_balance

    # -------------------------------
    # 5. RESULT STRUCTURE (Dashboard Ready)
    # -------------------------------
    return {
        "date": settlement_date,

        "withdrawal_gl": {
            "opening": withdrawal_gl.opening_balance,
            "acquirer": acquirer_amt,
            "issuer": issuer_amt,
            "expected_closing": expected_withdrawal_closing,
            "actual_closing": withdrawal_gl.closing_balance,
            "difference": withdrawal_diff,
        },

        "settlement_gl": {
            "opening": settlement_gl.opening_balance,
            "ntsl_settlement": final_settlement,
            "expected_closing": expected_settlement_closing,
            "actual_closing": settlement_gl.closing_balance,
            "difference": settlement_diff,
        }
    }