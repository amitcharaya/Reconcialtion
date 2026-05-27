"""
Service-layer business logic for the rgcs_reconciliation application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal

from cbs.models import RGCSCBSTransaction
from ndpg.models import RGCSRawTransaction
from switchlog.models import RGCSSwitchTransaction

from rgcs_reconciliation.models import RGCSReconciliationResult


def clean_rrn(value):
    if value is None:
        return ""
    return str(value).strip()


def clean_amount(value):
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


def amount_equal(*amounts):
    valid_amounts = [
        clean_amount(amount)
        for amount in amounts
        if amount is not None
    ]

    if not valid_amounts:
        return False

    return len(set(valid_amounts)) == 1


# Runs RGCS reconciliation for one selected transaction date.
# NDPG amount comparison uses actual_txn_amount from the RGCS NDPG model.
def run_rgcs_reconciliation(transaction_date):
    """
    RGCS reconciliation based on:
    1. Transaction Date
    2. RRN number
    """

    RGCSReconciliationResult.objects.filter(
        transaction_date=transaction_date
    ).delete()

    cbs_records = RGCSCBSTransaction.objects.filter(
        transaction_date=transaction_date
    )

    ndpg_records = RGCSRawTransaction.objects.filter(
        transaction_date=transaction_date
    )

    switch_records = RGCSSwitchTransaction.objects.filter(
        tranx_date=transaction_date
    )

    cbs_map = {}
    ndpg_map = {}
    switch_map = {}

    for txn in cbs_records:
        rrn = clean_rrn(txn.rrn)
        if rrn:
            cbs_map[rrn] = txn

    for txn in ndpg_records:
        rrn = clean_rrn(txn.rrn)
        if rrn:
            ndpg_map[rrn] = txn

    for txn in switch_records:
        rrn = clean_rrn(txn.rrn)
        if rrn:
            switch_map[rrn] = txn

    all_rrns = set(cbs_map.keys()) | set(ndpg_map.keys()) | set(switch_map.keys())

    summary = {
        "total": 0,
        "matched": 0,
        "amount_mismatch": 0,
        "cbs_only": 0,
        "ndpg_only": 0,
        "switch_only": 0,
        "zero_amount_ignored": 0,
        "cbs_ndpg_only": 0,
        "cbs_switch_only": 0,
        "ndpg_switch_only": 0,
    }

    for rrn in all_rrns:

        cbs_txn = cbs_map.get(rrn)
        ndpg_txn = ndpg_map.get(rrn)
        switch_txn = switch_map.get(rrn)

        cbs_amount = clean_amount(cbs_txn.transaction_amount) if cbs_txn else None
        ndpg_amount = clean_amount(ndpg_txn.actual_txn_amount) if ndpg_txn else None
        switch_amount = clean_amount(switch_txn.amount_approved) if switch_txn else None

        if amount_equal(cbs_amount or 0, ndpg_amount or 0, switch_amount or 0) and (cbs_amount or Decimal("0.00")) == Decimal("0.00") and (ndpg_amount or Decimal("0.00")) == Decimal("0.00") and (switch_amount or Decimal("0.00")) == Decimal("0.00"):
            summary["zero_amount_ignored"] += 1
            continue

        if cbs_txn and ndpg_txn and switch_txn:

            if amount_equal(cbs_amount, ndpg_amount, switch_amount):
                status = "MATCHED"
                remarks = "CBS, NDPG and Switch matched by transaction date and RRN."
                summary["matched"] += 1
            else:
                status = "AMOUNT_MISMATCH"
                remarks = "RRN matched in all sources but amount is different."
                summary["amount_mismatch"] += 1

        elif cbs_txn and ndpg_txn and not switch_txn:
            status = "CBS_NDPG_ONLY"
            remarks = "Transaction found in CBS and NDPG but not found in Switch."
            summary["cbs_ndpg_only"] += 1

        elif cbs_txn and switch_txn and not ndpg_txn:
            status = "CBS_SWITCH_ONLY"
            remarks = "Transaction found in CBS and Switch but not found in NDPG."
            summary["cbs_switch_only"] += 1

        elif ndpg_txn and switch_txn and not cbs_txn:
            status = "NDPG_SWITCH_ONLY"
            remarks = "Transaction found in NDPG and Switch but not found in CBS."
            summary["ndpg_switch_only"] += 1

        elif cbs_txn and not ndpg_txn and not switch_txn:
            status = "CBS_ONLY"
            remarks = "Transaction found only in CBS."
            summary["cbs_only"] += 1

        elif ndpg_txn and not cbs_txn and not switch_txn:
            status = "NDPG_ONLY"
            remarks = "Transaction found only in NDPG."
            summary["ndpg_only"] += 1

        else:
            status = "SWITCH_ONLY"
            remarks = "Transaction found only in Switch."
            summary["switch_only"] += 1

        RGCSReconciliationResult.objects.create(
            transaction_date=transaction_date,
            rrn=rrn,
            cbs_transaction_id=cbs_txn.id if cbs_txn else None,
            ndpg_transaction_id=ndpg_txn.id if ndpg_txn else None,
            switch_transaction_id=switch_txn.id if switch_txn else None,
            cbs_amount=cbs_amount,
            ndpg_amount=ndpg_amount,
            switch_amount=switch_amount,
            status=status,
            remarks=remarks,
        )

        summary["total"] += 1

    return summary