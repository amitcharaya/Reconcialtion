"""
Service-layer business logic for the disputes application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from disputes.models import ATMDisputeCase, RGCSDisputeCase, IMPSDisputeCase
from reconciliation.models import ATMReconciliationResult
from rgcs_reconciliation.models import RGCSReconciliationResult
from imps_reconciliation.models import IMPSReconciliationResult


ATM_NO_DISPUTE_STATUSES = {
    "MATCHED_ALL",
    "MATCHED_ONUS",
    "CBS_AUTO_REVERSED",
    "SWITCH_WITHDRAWAL_REVERSED",
    "FAILED_REVERSED_NO_DISPUTE",
    "FAILED_NDPG_ONLY",
    "SWITCH_ONLY_DECLINED",
    "NDPG_SWITCH_ONLY_0_AMOUNT",
    "AUTO_MATCHED_NEXT_DAY_NDPG",
}

RGCS_NO_DISPUTE_STATUSES = {
    "MATCHED",
}

IMPS_NO_DISPUTE_STATUSES = {
    "MATCHED_ALL",
    "CBS_AUTO_REVERSED",
}


def get_dispute_transaction_date(value):
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date()
    return value



def is_zero_exposure(*amounts):
    """Return True when all available source amounts are zero/blank.

    Such records are technical/non-financial exposure rows and must not become
    dispute cases. None is treated as zero for this check.
    """
    for amount in amounts:
        if amount is None:
            continue
        try:
            if amount != 0 and str(amount).strip() not in {"", "0", "0.0", "0.00"}:
                return False
        except Exception:
            return False
    return True

def first_amount(*amounts):
    for amount in amounts:
        if amount is not None:
            return amount
    return 0


def cleanup_no_dispute_cases(transaction_date=None):
    qs = ATMDisputeCase.objects.filter(source_status__in=ATM_NO_DISPUTE_STATUSES)
    if transaction_date:
        qs = qs.filter(transaction_date=get_dispute_transaction_date(transaction_date))
    qs.delete()


def create_dispute_cases(transaction_date=None):
    """Create ATM dispute cases for real financial exposure records."""
    cleanup_no_dispute_cases(transaction_date)

    qs = ATMReconciliationResult.objects.all()
    if transaction_date:
        qs = qs.filter(transaction_date=transaction_date)

    created = 0
    for result in qs:
        status = (result.status or "").strip()
        if status in ATM_NO_DISPUTE_STATUSES:
            continue

        if is_zero_exposure(result.cbs_amount, result.ndpg_amount, result.switch_amount):
            continue

        dispute_date = get_dispute_transaction_date(result.transaction_date)
        already_exists = ATMDisputeCase.objects.filter(
            transaction_date=dispute_date,
            stan_no=result.stan_no,
            rrn=result.rrn,
            source_status=status,
        ).exists()
        if already_exists:
            continue

        ATMDisputeCase.objects.create(
            transaction_date=dispute_date,
            stan_no=result.stan_no,
            rrn=result.rrn,
            disputed_amount=first_amount(result.cbs_amount, result.ndpg_amount, result.switch_amount),
            source_status=status,
            dispute_reason=result.remarks,
            case_status="OPEN",
        )
        created += 1

    cleanup_no_dispute_cases(transaction_date)
    return created


def cleanup_rgcs_no_dispute_cases(transaction_date=None):
    qs = RGCSDisputeCase.objects.filter(source_status__in=RGCS_NO_DISPUTE_STATUSES)
    if transaction_date:
        qs = qs.filter(transaction_date=get_dispute_transaction_date(transaction_date))
    qs.delete()


# Creates RGCS dispute cases only for unmatched transactions that represent
# financial exposure. Zero amount cases across all sources are ignored.
def create_rgcs_dispute_cases(transaction_date=None):
    """
    Create RGCS disputes from unmatched / financial-exposure reconciliation rows.
    Any RGCS status other than MATCHED is treated as financial exposure.
    """
    cleanup_rgcs_no_dispute_cases(transaction_date)

    qs = RGCSReconciliationResult.objects.all()
    if transaction_date:
        qs = qs.filter(transaction_date=transaction_date)

    created = 0
    for result in qs:
        status = (result.status or "").strip()
        if status in RGCS_NO_DISPUTE_STATUSES:
            continue

        if is_zero_exposure(result.cbs_amount, result.ndpg_amount, result.switch_amount):
            continue

        dispute_date = get_dispute_transaction_date(result.transaction_date)
        already_exists = RGCSDisputeCase.objects.filter(
            transaction_date=dispute_date,
            rrn=result.rrn,
            source_status=status,
        ).exists()
        if already_exists:
            continue

        RGCSDisputeCase.objects.create(
            transaction_date=dispute_date,
            rrn=result.rrn,
            disputed_amount=first_amount(result.cbs_amount, result.ndpg_amount, result.switch_amount),
            source_status=status,
            dispute_reason=result.remarks,
            case_status="OPEN",
        )
        created += 1

    cleanup_rgcs_no_dispute_cases(transaction_date)
    return created


def cleanup_imps_no_dispute_cases(transaction_date=None):
    qs = IMPSDisputeCase.objects.filter(source_status__in=IMPS_NO_DISPUTE_STATUSES)
    if transaction_date:
        qs = qs.filter(transaction_date=get_dispute_transaction_date(transaction_date))
    qs.delete()


# Creates IMPS dispute cases only for unmatched transactions that represent
# financial exposure. This mirrors the ATM dispute creation approach.
def create_imps_dispute_cases(transaction_date=None):
    """
    Create IMPS disputes from unmatched / financial-exposure reconciliation rows.
    This matches the IMPS MIS exposure logic: all statuses except MATCHED_ALL
    and CBS_AUTO_REVERSED are dispute-worthy.
    """
    cleanup_imps_no_dispute_cases(transaction_date)

    qs = IMPSReconciliationResult.objects.all()
    if transaction_date:
        qs = qs.filter(transaction_date=transaction_date)

    created = 0
    for result in qs:
        status = (result.status or "").strip()
        if status in IMPS_NO_DISPUTE_STATUSES:
            continue

        if is_zero_exposure(result.cbs_amount, result.switch_amount, result.ndpg_amount):
            continue

        dispute_date = get_dispute_transaction_date(result.transaction_date)
        serial_no = result.transaction_serial_number or result.rrn or ""

        already_exists = IMPSDisputeCase.objects.filter(
            transaction_date=dispute_date,
            transaction_serial_number=serial_no,
            source_status=status,
        ).exists()
        if already_exists:
            continue

        IMPSDisputeCase.objects.create(
            transaction_date=dispute_date,
            transaction_serial_number=serial_no,
            rrn=result.rrn,
            disputed_amount=first_amount(result.cbs_amount, result.switch_amount, result.ndpg_amount),
            source_status=status,
            dispute_reason=result.reason,
            case_status="OPEN",
        )
        created += 1

    cleanup_imps_no_dispute_cases(transaction_date)
    return created
