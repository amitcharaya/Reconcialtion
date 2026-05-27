"""
Python module used by the reconciliation application.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal

from cbs.models import CBSATMTransaction
from ndpg.models import NDPGATMTransaction
from switchlog.models import SwitchATMTransaction

from .models import ATMReconciliationResult
from .utils import normalize_date

from reconciliation.services.transaction_normalizer import (
    normalize_cbs_transaction,
    normalize_switch_transaction,
    normalize_ndpg_transaction,
)

from disputes.services.dispute_service import create_dispute_cases

def mark_failed_reversed_no_dispute(transaction_date):
    results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status__in=[
            "PENDING_NDPG_NEXT_DAY",
            "CBS_SWITCH_ONLY",
            "AMOUNT_MISMATCH",
        ]
    )

    for result in results:
        if not result.stan_no:
            continue

        amount = normalize_amount(
            result.cbs_amount or result.switch_amount
        )

        cbs_debit = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            dr_cr_flag__iexact="D",
            txn_amount=amount
        ).first()

        cbs_credit = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            dr_cr_flag__iexact="C",
            txn_amount=amount
        ).first()

        switch_withdrawal = SwitchATMTransaction.objects.filter(
            transaction_date=transaction_date,
            stan_no=result.stan_no,
            transaction_type__iexact="Withdrawal",
            transaction_amount=amount
        ).first()

        switch_reversal_query = SwitchATMTransaction.objects.filter(
            transaction_type__iexact="Withdrawal Reversal",
            transaction_amount=amount
        )

        if result.rrn:
            switch_reversal_query = switch_reversal_query.filter(
                rrn=result.rrn
            )
        else:
            switch_reversal_query = switch_reversal_query.filter(
                transaction_date=transaction_date,
                stan_no=result.stan_no
            )

        switch_reversal = switch_reversal_query.first()

        ndpg_failed = False

        if result.rrn:
            ndpg_failed = NDPGATMTransaction.objects.filter(
                transaction_serial_number=result.rrn
            ).exclude(
                response_code="00"
            ).exists()

        if cbs_debit and cbs_credit and switch_withdrawal and switch_reversal:
            result.status = "FAILED_REVERSED_NO_DISPUTE"
            result.remarks = (
                "CBS debit and credit found with same amount; "
                "Switch withdrawal and withdrawal reversal found with same amount. "
            )

            if ndpg_failed:
                result.remarks += (
                    "NDPG failed response also found. "
                    "Transaction failed/reversed at all applicable stages. "
                    "No dispute required."
                )
            else:
                result.remarks += (
                    "NDPG successful record not found. "
                    "Transaction reversed at CBS and Switch. "
                    "No dispute required."
                )

            result.save()

def mark_cbs_switch_reversed_no_dispute(transaction_date):
    results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status="CBS_SWITCH_ONLY"
    )

    for result in results:
        if not result.stan_no:
            continue

        cbs_debit = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            dr_cr_flag__iexact="D"
        ).first()

        cbs_credit = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            dr_cr_flag__iexact="C"
        ).first()

        switch_withdrawal = SwitchATMTransaction.objects.filter(
            transaction_date=transaction_date,
            stan_no=result.stan_no,
            transaction_type__iexact="Withdrawal"
        ).first()

        switch_reversal_query = SwitchATMTransaction.objects.filter(
            transaction_date=transaction_date,
            transaction_type__iexact="Withdrawal Reversal"
        )

        if result.rrn:
            switch_reversal_query = switch_reversal_query.filter(rrn=result.rrn)
        else:
            switch_reversal_query = switch_reversal_query.filter(stan_no=result.stan_no)

        switch_reversal = switch_reversal_query.first()

        if cbs_debit and cbs_credit and switch_withdrawal and switch_reversal:
            cbs_debit_amount = normalize_amount(cbs_debit.txn_amount)
            cbs_credit_amount = normalize_amount(cbs_credit.txn_amount)
            switch_withdrawal_amount = normalize_amount(
                switch_withdrawal.transaction_amount
            )
            switch_reversal_amount = normalize_amount(
                switch_reversal.transaction_amount
            )

            if (
                cbs_debit_amount == cbs_credit_amount
                and switch_withdrawal_amount == switch_reversal_amount
                and cbs_debit_amount == switch_withdrawal_amount
            ):
                result.status = "FAILED_REVERSED_NO_DISPUTE"
                result.remarks = (
                    "CBS debit and credit found with same amount; "
                    "Switch withdrawal and withdrawal reversal found with same amount; "
                    "NDPG not present. Transaction failed/reversed at both CBS and Switch. "
                    "No dispute required."
                )
                result.save()
def normalize_amount(amount):
    if amount is None:
        return None

    return Decimal(str(amount)).quantize(Decimal("0.01"))


def build_key(date, reference, amount):
    amount = normalize_amount(amount)
    normalized_date = normalize_date(date)

    if not normalized_date or not reference or amount is None:
        return None

    return f"{normalized_date}|{str(reference).strip()}|{amount}"


def decide_reconciliation_status(cbs_txn=None, switch_txn=None, ndpg_txn=None):
    cbs_info = normalize_cbs_transaction(cbs_txn)
    switch_info = normalize_switch_transaction(switch_txn)
    ndpg_info = normalize_ndpg_transaction(ndpg_txn)

    cbs_present = cbs_txn is not None
    switch_present = switch_txn is not None
    ndpg_present = ndpg_txn is not None

    cbs_amount = cbs_info["amount"] if cbs_info else None
    switch_amount = switch_info["amount"] if switch_info else None
    ndpg_amount = ndpg_info["amount"] if ndpg_info else None

    # CASE 1: CBS + Switch + NDPG present
    if cbs_present and switch_present and ndpg_present:

        if (
            cbs_info["is_reversal"]
            and switch_info["is_reversal"]
            and not ndpg_info["is_success"]
        ):
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Transaction reversed at CBS and Switch and failed at NDPG. No dispute required."
            )

        if cbs_info["is_reversal"] and switch_info["is_reversal"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Transaction reversed at both CBS and Switch. No dispute required."
            )

        if cbs_info["is_reversal"] and not ndpg_info["is_success"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "CBS reversal and NDPG failed response found. No dispute required."
            )

        if switch_info["is_reversal"] and not ndpg_info["is_success"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Switch reversal and NDPG failed response found. No dispute required."
            )

        if (
            cbs_info["is_success"]
            and switch_info["is_success"]
            and ndpg_info["is_success"]
        ):
            if cbs_amount == switch_amount == ndpg_amount:
                return (
                    "MATCHED_ALL",
                    "CBS debit, Switch withdrawal and NDPG success matched with same amount."
                )

            return (
                "AMOUNT_MISMATCH",
                "CBS, Switch and NDPG are successful but amount mismatch found."
            )

        if cbs_info["is_reversal"] or switch_info["is_reversal"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Transaction has reversal indicator. No dispute required."
            )

        if not ndpg_info["is_success"]:
            return (
                "FAILED_NDPG_ONLY",
                f"NDPG transaction failed with response code {ndpg_txn.response_code}."
            )

        return (
            "AMOUNT_MISMATCH",
            "Transaction contains failed/reversal indicator."
        )

    # CASE 2: CBS only
    if cbs_present and not switch_present and not ndpg_present:
        if cbs_info["is_reversal"]:
            return (
                "CBS_AUTO_REVERSED",
                "CBS credit/reversal found without Switch/NDPG."
            )

        return (
            "CBS_ONLY",
            "CBS debit transaction found only in CBS."
        )

    # CASE 3: NDPG only
    if ndpg_present and not cbs_present and not switch_present:
        if not ndpg_info["is_success"]:
            return (
                "FAILED_NDPG_ONLY",
                f"NDPG-only transaction failed with response code {ndpg_txn.response_code}."
            )

        return (
            "NDPG_ONLY",
            "Successful NDPG transaction found only in NDPG."
        )

    # CASE 4: Switch only
    if switch_present and not cbs_present and not ndpg_present:
        if switch_info["is_reversal"] or switch_amount == Decimal("0.00"):
            return (
                "SWITCH_ONLY_DECLINED",
                "Switch-only transaction is reversal or zero amount. No dispute required."
            )

        return (
            "SWITCH_ONLY",
            "Successful Switch withdrawal found only in Switch."
        )

    # CASE 5: CBS + Switch only
    # CASE 5: CBS + Switch only
    if cbs_present and switch_present and not ndpg_present:

        cbs_file_type = (cbs_txn.file_type or "").upper().strip()

        if cbs_file_type == "O":
            if cbs_info["is_success"] and switch_info["is_success"]:
                if cbs_amount == switch_amount:
                    return (
                        "MATCHED_ONUS",
                        "On-us transaction matched between CBS and Switch. NDPG is not expected."
                    )

                return (
                    "AMOUNT_MISMATCH",
                    "On-us transaction found in CBS and Switch but amount mismatch."
                )

            return (
                "CBS_SWITCH_ONLY",
                "On-us transaction found in CBS and Switch but not successful at both sources."
            )

        if cbs_info["is_reversal"] and switch_info["is_reversal"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Transaction reversed at both CBS and Switch. NDPG missing. No dispute required."
            )

        if cbs_info["is_reversal"] and switch_info["is_success"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "CBS credit/reversal found and Switch record present. NDPG missing. No dispute required."
            )

        if cbs_info["is_success"] and switch_info["is_reversal"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Switch withdrawal reversal found with CBS record. NDPG missing. No dispute required."
            )

        if cbs_info["is_success"] and switch_info["is_success"]:
            if cbs_amount == switch_amount:
                return (
                    "PENDING_NDPG_NEXT_DAY",
                    "CBS and Switch matched successfully. NDPG not found on transaction date. Pending next-day NDPG settlement."
                )

            return (
                "AMOUNT_MISMATCH",
                "CBS and Switch successful but amount mismatch found."
            )

        return (
            "CBS_SWITCH_ONLY",
            "CBS and Switch found without NDPG."
        )
    # CASE 6: CBS + NDPG only
    if cbs_present and ndpg_present and not switch_present:

        if cbs_info["is_reversal"] and not ndpg_info["is_success"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "CBS reversal and NDPG failed response found. Switch missing. No dispute required."
            )

        if cbs_info["is_success"] and ndpg_info["is_success"]:
            if cbs_amount == ndpg_amount:
                return (
                    "CBS_NDPG_ONLY",
                    "CBS debit and NDPG successful transaction matched, but Switch missing."
                )

            return (
                "AMOUNT_MISMATCH",
                "CBS and NDPG successful but amount mismatch found."
            )

        if cbs_info["is_reversal"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "CBS reversal found with NDPG record. No dispute required."
            )

        if not ndpg_info["is_success"]:
            return (
                "FAILED_NDPG_ONLY",
                f"NDPG transaction failed with response code {ndpg_txn.response_code}."
            )

        return (
            "CBS_NDPG_ONLY",
            "CBS and NDPG found without Switch."
        )

    # CASE 7: NDPG + Switch only
    if ndpg_present and switch_present and not cbs_present:

        if switch_info["is_reversal"] and not ndpg_info["is_success"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Switch reversal and NDPG failed response found. CBS missing. No dispute required."
            )

        if ndpg_amount == Decimal("0.00") and switch_amount == Decimal("0.00"):
            return (
                "NDPG_SWITCH_ONLY_0_AMOUNT",
                "NDPG and Switch found with zero amount in both sources."
            )

        if ndpg_info["is_success"] and switch_info["is_success"]:
            if ndpg_amount == switch_amount:
                return (
                    "NDPG_SWITCH_ONLY",
                    "NDPG successful transaction and Switch withdrawal matched, but CBS missing."
                )

            return (
                "AMOUNT_MISMATCH",
                "NDPG and Switch successful but amount mismatch found."
            )

        if switch_info["is_reversal"]:
            return (
                "FAILED_REVERSED_NO_DISPUTE",
                "Switch withdrawal reversal found with NDPG record. No dispute required."
            )

        if not ndpg_info["is_success"]:
            return (
                "FAILED_NDPG_ONLY",
                f"NDPG transaction failed with response code {ndpg_txn.response_code}."
            )

        return (
            "NDPG_SWITCH_ONLY",
            "NDPG and Switch found without CBS."
        )

    return (
        "AMOUNT_MISMATCH",
        "Unable to classify transaction."
    )


def create_result(
    transaction_date,
    stan_no=None,
    rrn=None,
    cbs_txn=None,
    ndpg_txn=None,
    switch_txn=None,
    matched_by=None,
    remarks=None,
):
    status, status_remarks = decide_reconciliation_status(
        cbs_txn=cbs_txn,
        switch_txn=switch_txn,
        ndpg_txn=ndpg_txn,
    )

    final_remarks = remarks or ""

    if status_remarks:
        if final_remarks:
            final_remarks = f"{final_remarks} | {status_remarks}"
        else:
            final_remarks = status_remarks

    ATMReconciliationResult.objects.create(
        transaction_date=normalize_date(transaction_date),
        stan_no=stan_no,
        rrn=rrn,

        cbs_amount=cbs_txn.txn_amount if cbs_txn else None,
        ndpg_amount=ndpg_txn.actual_transaction_amount if ndpg_txn else None,
        switch_amount=switch_txn.transaction_amount if switch_txn else None,

        cbs_present=cbs_txn is not None,
        ndpg_present=ndpg_txn is not None,
        switch_present=switch_txn is not None,

        matched_by=matched_by,
        status=status,
        remarks=final_remarks,
    )


def mark_onus_matched(transaction_date):
    results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status__in=[
            "CBS_SWITCH_ONLY",
            "PENDING_NDPG_NEXT_DAY",
        ]
    )

    for result in results:
        if not result.stan_no:
            continue

        cbs_txn = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            file_type__iexact="O",
            dr_cr_flag__iexact="D"
        ).first()

        switch_txn = SwitchATMTransaction.objects.filter(
            transaction_date=transaction_date,
            stan_no=result.stan_no,
            transaction_type__iexact="Withdrawal",
            void_code="0"
        ).first()

        if not cbs_txn or not switch_txn:
            continue

        cbs_amount = normalize_amount(cbs_txn.txn_amount)
        switch_amount = normalize_amount(switch_txn.transaction_amount)

        if cbs_amount == switch_amount:
            result.status = "MATCHED_ONUS"
            result.cbs_present = True
            result.switch_present = True
            result.ndpg_present = False
            result.cbs_amount = cbs_txn.txn_amount
            result.switch_amount = switch_txn.transaction_amount
            result.ndpg_amount = None
            result.matched_by = "ONUS_CBS_SWITCH"
            result.remarks = (
                "On-us transaction matched between CBS and Switch. "
                "NDPG record is not expected for on-us transactions."
            )
            result.save()

def mark_switch_only_declined(transaction_date):
    results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status="SWITCH_ONLY"
    )

    for result in results:
        switch_amount = result.switch_amount or Decimal("0.00")

        if switch_amount == Decimal("0.00"):
            result.status = "SWITCH_ONLY_DECLINED"
            result.remarks = (
                "Switch-only transaction has zero approved amount. "
                "Marked as SWITCH_ONLY_DECLINED."
            )
            result.save()


def mark_ndpg_switch_only_zero_amount(transaction_date):
    results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status="NDPG_SWITCH_ONLY"
    )

    for result in results:
        ndpg_amount = result.ndpg_amount or Decimal("0.00")
        switch_amount = result.switch_amount or Decimal("0.00")

        if ndpg_amount == Decimal("0.00") and switch_amount == Decimal("0.00"):
            result.status = "NDPG_SWITCH_ONLY_0_AMOUNT"
            result.remarks = (
                "NDPG and Switch transaction found with zero amount in both sources. "
                "Marked as NDPG_SWITCH_ONLY_0_AMOUNT."
            )
            result.save()


def mark_failed_ndpg_only(transaction_date):
    ndpg_only_results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status="NDPG_ONLY"
    )

    for result in ndpg_only_results:
        if not result.rrn:
            continue

        ndpg_txn = NDPGATMTransaction.objects.filter(
            transaction_date=transaction_date,
            transaction_serial_number=result.rrn
        ).first()

        if ndpg_txn and ndpg_txn.response_code != "00":
            result.status = "FAILED_NDPG_ONLY"
            result.remarks = (
                f"NDPG-only transaction failed with response code "
                f"{ndpg_txn.response_code}."
            )
            result.save()


def mark_cbs_auto_reversed(transaction_date):
    cbs_only_results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status="CBS_ONLY"
    )

    for result in cbs_only_results:
        if not result.stan_no:
            continue

        debit_txn = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            dr_cr_flag__iexact="D"
        ).first()

        credit_txn = CBSATMTransaction.objects.filter(
            txn_date=transaction_date,
            stan_no=result.stan_no,
            dr_cr_flag__iexact="C"
        ).first()

        if debit_txn and credit_txn:
            debit_amount = normalize_amount(debit_txn.txn_amount)
            credit_amount = normalize_amount(credit_txn.txn_amount)

            if debit_amount == credit_amount:
                result.status = "CBS_AUTO_REVERSED"
                result.remarks = (
                    "CBS-only transaction has both debit and credit entries "
                    "with same STAN and amount. Marked as CBS_AUTO_REVERSED."
                )
                result.save()


def mark_switch_withdrawal_reversed(transaction_date):
    switch_only_results = ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date,
        status="SWITCH_ONLY"
    )

    for result in switch_only_results:
        if not result.stan_no and not result.rrn:
            continue

        query = SwitchATMTransaction.objects.filter(
            transaction_date=transaction_date
        )

        if result.stan_no:
            query = query.filter(stan_no=result.stan_no)

        if result.rrn:
            query = query.filter(rrn=result.rrn)

        withdrawal_txn = query.filter(
            transaction_type__iexact="Withdrawal"
        ).first()

        reversal_txn = query.filter(
            transaction_type__iexact="Withdrawal Reversal"
        ).first()

        if withdrawal_txn and reversal_txn:
            withdrawal_amount = normalize_amount(withdrawal_txn.transaction_amount)
            reversal_amount = normalize_amount(reversal_txn.transaction_amount)

            if withdrawal_amount == reversal_amount:
                result.status = "SWITCH_WITHDRAWAL_REVERSED"
                result.remarks = (
                    "Switch withdrawal and withdrawal reversal found with same "
                    "STAN/RRN and amount."
                )
                result.save()


def run_post_reconciliation_rules(transaction_date):
    mark_failed_reversed_no_dispute(transaction_date=transaction_date)

    mark_cbs_auto_reversed(transaction_date=transaction_date)
    mark_failed_ndpg_only(transaction_date=transaction_date)
    mark_ndpg_switch_only_zero_amount(transaction_date=transaction_date)
    mark_switch_only_declined(transaction_date=transaction_date)
    mark_switch_withdrawal_reversed(transaction_date=transaction_date)
    mark_onus_matched(transaction_date=transaction_date)

    mark_failed_reversed_no_dispute(transaction_date=transaction_date)

def run_atm_reconciliation(transaction_date):
    transaction_date = normalize_date(transaction_date)

    ATMReconciliationResult.objects.filter(
        transaction_date=transaction_date
    ).delete()

    cbs_records = CBSATMTransaction.objects.filter(
        txn_date=transaction_date
    )

    switch_records = SwitchATMTransaction.objects.filter(
        transaction_date=transaction_date
    )

    ndpg_records = NDPGATMTransaction.objects.filter(
        transaction_date=transaction_date
    )

    switch_stan_map = {}
    switch_rrn_map = {}
    ndpg_rrn_map = {}

    used_cbs_ids = set()
    used_switch_ids = set()
    used_ndpg_ids = set()

    for txn in switch_records:
        stan_key = build_key(
            txn.transaction_date,
            txn.stan_no,
            txn.transaction_amount
        )

        rrn_key = build_key(
            txn.transaction_date,
            txn.rrn,
            txn.transaction_amount
        )

        if stan_key:
            switch_stan_map[stan_key] = txn

        if rrn_key:
            switch_rrn_map[rrn_key] = txn

    for txn in ndpg_records:
        rrn_key = build_key(
            txn.transaction_date,
            txn.transaction_serial_number,
            txn.actual_transaction_amount
        )

        if rrn_key:
            ndpg_rrn_map[rrn_key] = txn

    # Stage 1: CBS as base
    for cbs_txn in cbs_records:
        used_cbs_ids.add(cbs_txn.id)

        switch_key = build_key(
            cbs_txn.txn_date,
            cbs_txn.stan_no,
            cbs_txn.txn_amount
        )

        switch_txn = switch_stan_map.get(switch_key)

        ndpg_txn = None
        rrn = None
        matched_by = None
        remarks = None

        if switch_txn:
            used_switch_ids.add(switch_txn.id)

            rrn = switch_txn.rrn
            matched_by = "CBS_STAN_TO_SWITCH"

            ndpg_key = build_key(
                cbs_txn.txn_date,
                rrn,
                cbs_txn.txn_amount
            )

            ndpg_txn = ndpg_rrn_map.get(ndpg_key)

            if ndpg_txn:
                used_ndpg_ids.add(ndpg_txn.id)
                matched_by = "CBS_STAN_SWITCH_RRN_NDPG"
                remarks = (
                    "CBS matched with Switch using STAN; "
                    "NDPG matched using Switch RRN."
                )
            else:
                remarks = (
                    "CBS matched with Switch using STAN, but no NDPG "
                    "match found using Switch RRN."
                )
        else:
            remarks = "No Switch match found using CBS STAN."

        create_result(
            transaction_date=cbs_txn.txn_date,
            stan_no=cbs_txn.stan_no,
            rrn=rrn,
            cbs_txn=cbs_txn,
            ndpg_txn=ndpg_txn,
            switch_txn=switch_txn,
            matched_by=matched_by,
            remarks=remarks,
        )

    # Stage 2: NDPG records not matched through CBS/Switch
    for ndpg_txn in ndpg_records:

        # Skip only if already matched in Stage 1
        if ndpg_txn.id in used_ndpg_ids:
            continue

        rrn = ndpg_txn.transaction_serial_number

        switch_txn = None

        # Try Switch match only if RRN exists
        if rrn:
            rrn_key = build_key(
                ndpg_txn.transaction_date,
                rrn,
                ndpg_txn.actual_transaction_amount
            )

            switch_txn = switch_rrn_map.get(rrn_key)

        # CASE A: NDPG + Switch found
        if switch_txn and switch_txn.id not in used_switch_ids:
            used_switch_ids.add(switch_txn.id)

            create_result(
                transaction_date=ndpg_txn.transaction_date,
                stan_no=switch_txn.stan_no,
                rrn=rrn,
                cbs_txn=None,
                ndpg_txn=ndpg_txn,
                switch_txn=switch_txn,
                matched_by="NDPG_RRN_TO_SWITCH",
                remarks=(
                    "NDPG matched with Switch using RRN, but CBS record not found."
                ),
            )

        # CASE B: Pure NDPG only
        else:
            create_result(
                transaction_date=ndpg_txn.transaction_date,
                stan_no=getattr(ndpg_txn, "stan_no", None),
                rrn=rrn,
                cbs_txn=None,
                ndpg_txn=ndpg_txn,
                switch_txn=None,
                matched_by="NDPG_ONLY",
                remarks=(
                    "NDPG transaction found only in NDPG file "
                    "(including cycle-only transaction)."
                ),
            )

        # IMPORTANT:
        # Mark used AFTER create_result
        used_ndpg_ids.add(ndpg_txn.id)

    # Stage 3: Switch records not matched with CBS or NDPG
    for switch_txn in switch_records:
        if switch_txn.id in used_switch_ids:
            continue

        create_result(
            transaction_date=switch_txn.transaction_date,
            stan_no=switch_txn.stan_no,
            rrn=switch_txn.rrn,
            cbs_txn=None,
            ndpg_txn=None,
            switch_txn=switch_txn,
            matched_by=None,
            remarks="Switch record not found in CBS or NDPG.",
        )

        used_switch_ids.add(switch_txn.id)

    run_post_reconciliation_rules(transaction_date=transaction_date)
    create_dispute_cases(transaction_date=transaction_date)
