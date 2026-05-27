"""
Service-layer business logic for the reconciliation application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from reconciliation.models import ATMReconciliationResult
from ndpg.models import NDPGATMTransaction
from disputes.models import ATMDisputeCase
from reconciliation.engine import normalize_amount


def auto_match_next_day_ndpg(settlement_date):
    """
    Match previous pending CBS+Switch transactions with NDPG records
    uploaded in next day's settlement file.

    Example:
    CBS/Switch transaction_date = 13-05-2026
    NDPG settlement_date = 14-05-2026
    """

    ndpg_records = NDPGATMTransaction.objects.filter(
        card_acceptor_settlement_date=settlement_date,
        response_code="00"
    )

    for ndpg_txn in ndpg_records:
        rrn = ndpg_txn.transaction_serial_number
        amount = normalize_amount(ndpg_txn.actual_transaction_amount)

        if not rrn:
            continue

        pending_result = ATMReconciliationResult.objects.filter(
            rrn=rrn,
            status="PENDING_NDPG_NEXT_DAY",
            switch_amount=amount
        ).first()

        if not pending_result:
            continue

        pending_result.ndpg_present = True
        pending_result.ndpg_amount = ndpg_txn.actual_transaction_amount
        pending_result.status = "AUTO_MATCHED_NEXT_DAY_NDPG"
        pending_result.remarks = (
            f"{pending_result.remarks or ''} | "
            f"Matched with NDPG next-day settlement file dated {settlement_date}."
        )
        pending_result.save()

        ATMDisputeCase.objects.filter(
            rrn=rrn,
            source_status="PENDING_NDPG_NEXT_DAY"
        ).update(
            case_status="CLOSED",
            remarks=(
                "Automatically closed after matching with next-day NDPG settlement."
            )
        )