"""
Python module used by the imps_reconciliation application.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal
from django.db import transaction

from cbs.models import CBSIMPSTransaction
from switchlog.models import SwitchIMPSTransaction
from ndpg.models import NDPGIMPSRawTransaction
from .models import IMPSReconciliationResult


def normalize(value):
    if value is None:
        return ""
    return str(value).strip()


def amount_equal(amount1, amount2):
    if amount1 is None or amount2 is None:
        return False

    return Decimal(amount1) == Decimal(amount2)


def get_switch_by_rrn(transaction_serial_number, transaction_date):
    """
    IMPS matching rule:

    CBS transaction_serial_number
    =
    Switch rrn

    Only financial Switch transactions are considered for reconciliation.
    Non-financial transactions remain only for MIS.
    """

    return SwitchIMPSTransaction.objects.filter(
        rrn=transaction_serial_number,
        transaction_datetime__date=transaction_date,
        transaction_amount__gt=0
    ).first()


def get_ndpg_by_serial(transaction_serial_number, transaction_date):
    """
    IMPS matching rule:

    CBS transaction_serial_number
    =
    NDPG transaction_serial_number
    """

    return NDPGIMPSRawTransaction.objects.filter(
        transaction_serial_number=transaction_serial_number,
        transaction_date=transaction_date
    ).first()


def is_cbs_auto_reversed(cbs_txn):
    """
    Same transaction_serial_number having both Debit and Credit
    means CBS auto-reversed.
    """

    debit_exists = CBSIMPSTransaction.objects.filter(
        transaction_serial_number=cbs_txn.transaction_serial_number,
        transaction_date=cbs_txn.transaction_date,
        transaction_amount=cbs_txn.transaction_amount,
        dr_cr_flag="D"
    ).exists()

    credit_exists = CBSIMPSTransaction.objects.filter(
        transaction_serial_number=cbs_txn.transaction_serial_number,
        transaction_date=cbs_txn.transaction_date,
        transaction_amount=cbs_txn.transaction_amount,
        dr_cr_flag="C"
    ).exists()

    return debit_exists and credit_exists


def create_result(
    transaction_date,
    transaction_serial_number,
    status,
    cbs_txn=None,
    switch_txn=None,
    ndpg_txn=None,
    reason=""
):
    rrn = switch_txn.rrn if switch_txn else transaction_serial_number

    IMPSReconciliationResult.objects.update_or_create(
        transaction_date=transaction_date,
        transaction_serial_number=transaction_serial_number,
        status=status,
        defaults={
            "rrn": rrn,
            "cbs_transaction": cbs_txn,
            "switch_transaction": switch_txn,
            "ndpg_transaction": ndpg_txn,
            "cbs_amount": cbs_txn.transaction_amount if cbs_txn else None,
            "switch_amount": switch_txn.transaction_amount if switch_txn else None,
            "ndpg_amount": ndpg_txn.actual_transaction_amount if ndpg_txn else None,
            "reason": reason,
        }
    )


@transaction.atomic
def reconcile_imps_transactions(transaction_date):
    """
    Main IMPS reconciliation engine.

    Matching rule:

    CBSIMPSTransaction.transaction_serial_number
    =
    SwitchIMPSTransaction.rrn
    =
    NDPGIMPSRawTransaction.transaction_serial_number

    Important:
    Non-financial Switch transactions are not considered for reconciliation.
    They are shown only in MIS report.
    """

    IMPSReconciliationResult.objects.filter(
        transaction_date=transaction_date
    ).delete()

    cbs_transactions = CBSIMPSTransaction.objects.filter(
        transaction_date=transaction_date
    )

    processed_switch_ids = set()
    processed_ndpg_ids = set()

    for cbs_txn in cbs_transactions:
        serial_no = normalize(cbs_txn.transaction_serial_number)

        switch_txn = get_switch_by_rrn(
            transaction_serial_number=serial_no,
            transaction_date=transaction_date
        )

        ndpg_txn = get_ndpg_by_serial(
            transaction_serial_number=serial_no,
            transaction_date=transaction_date
        )

        if switch_txn:
            processed_switch_ids.add(switch_txn.id)

        if ndpg_txn:
            processed_ndpg_ids.add(ndpg_txn.id)

        if is_cbs_auto_reversed(cbs_txn):
            create_result(
                transaction_date=transaction_date,
                transaction_serial_number=serial_no,
                status="CBS_AUTO_REVERSED",
                cbs_txn=cbs_txn,
                switch_txn=switch_txn,
                ndpg_txn=ndpg_txn,
                reason="CBS has both debit and credit entry for the same IMPS transaction serial number."
            )
            continue

        if switch_txn and ndpg_txn:
            if (
                amount_equal(cbs_txn.transaction_amount, switch_txn.transaction_amount)
                and amount_equal(cbs_txn.transaction_amount, ndpg_txn.actual_transaction_amount)
            ):
                create_result(
                    transaction_date=transaction_date,
                    transaction_serial_number=serial_no,
                    status="MATCHED_ALL",
                    cbs_txn=cbs_txn,
                    switch_txn=switch_txn,
                    ndpg_txn=ndpg_txn,
                    reason="Transaction matched in CBS, Switch and NDPG."
                )
            else:
                create_result(
                    transaction_date=transaction_date,
                    transaction_serial_number=serial_no,
                    status="AMOUNT_MISMATCH",
                    cbs_txn=cbs_txn,
                    switch_txn=switch_txn,
                    ndpg_txn=ndpg_txn,
                    reason="Transaction found in CBS, Switch and NDPG but amount mismatch exists."
                )

        elif switch_txn and not ndpg_txn:
            create_result(
                transaction_date=transaction_date,
                transaction_serial_number=serial_no,
                status="CBS_SWITCH_ONLY",
                cbs_txn=cbs_txn,
                switch_txn=switch_txn,
                reason="Transaction found in CBS and Switch but not found in NDPG."
            )

        elif ndpg_txn and not switch_txn:
            create_result(
                transaction_date=transaction_date,
                transaction_serial_number=serial_no,
                status="CBS_NDPG_ONLY",
                cbs_txn=cbs_txn,
                ndpg_txn=ndpg_txn,
                reason="Transaction found in CBS and NDPG but not found in Switch."
            )

        else:
            create_result(
                transaction_date=transaction_date,
                transaction_serial_number=serial_no,
                status="CBS_ONLY",
                cbs_txn=cbs_txn,
                reason="Transaction found only in CBS."
            )

    # Switch-only reconciliation:
    # Only financial Switch transactions are considered.
    switch_transactions = SwitchIMPSTransaction.objects.filter(
        transaction_datetime__date=transaction_date,
        transaction_amount__gt=0
    ).exclude(id__in=processed_switch_ids).exclude(
    transaction_particulars="NEFT transaction").exclude(status="Error").exclude(transaction_particulars="Within Bank Transfer")

    for switch_txn in switch_transactions:
        serial_no = normalize(switch_txn.rrn)

        if not serial_no:
            serial_no = normalize(switch_txn.transaction_id)

        ndpg_txn = get_ndpg_by_serial(
            transaction_serial_number=serial_no,
            transaction_date=transaction_date
        )

        if ndpg_txn:
            processed_ndpg_ids.add(ndpg_txn.id)

            if amount_equal(
                switch_txn.transaction_amount,
                ndpg_txn.actual_transaction_amount
            ):
                create_result(
                    transaction_date=transaction_date,
                    transaction_serial_number=serial_no,
                    status="SWITCH_NDPG_ONLY",
                    switch_txn=switch_txn,
                    ndpg_txn=ndpg_txn,
                    reason="Transaction found in Switch and NDPG but not found in CBS."
                )
            else:
                create_result(
                    transaction_date=transaction_date,
                    transaction_serial_number=serial_no,
                    status="AMOUNT_MISMATCH",
                    switch_txn=switch_txn,
                    ndpg_txn=ndpg_txn,
                    reason="Transaction found in Switch and NDPG but amount mismatch exists."
                )

        else:
            create_result(
                transaction_date=transaction_date,
                transaction_serial_number=serial_no,
                status="SWITCH_ONLY",
                switch_txn=switch_txn,
                reason="Financial transaction found only in Switch."
            )

    ndpg_transactions = NDPGIMPSRawTransaction.objects.filter(
        transaction_date=transaction_date
    ).exclude(id__in=processed_ndpg_ids)

    for ndpg_txn in ndpg_transactions:
        serial_no = normalize(ndpg_txn.transaction_serial_number)

        if ndpg_txn.response_code and ndpg_txn.response_code != "00":
            status = "FAILED_NDPG_ONLY"
            reason = "Transaction found only in NDPG with failed response code."
        else:
            status = "NDPG_ONLY"
            reason = "Transaction found only in NDPG."

        create_result(
            transaction_date=transaction_date,
            transaction_serial_number=serial_no,
            status=status,
            ndpg_txn=ndpg_txn,
            reason=reason
        )

    return IMPSReconciliationResult.objects.filter(
        transaction_date=transaction_date
    ).count()