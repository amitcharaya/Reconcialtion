"""
Service-layer business logic for the reconciliation application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal


def safe_amount(value):
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(Decimal("0.01"))


def normalize_cbs_transaction(cbs_txn):
    """
    CBS:
    D = Debit
    C = Credit / reversal
    """

    if not cbs_txn:
        return None

    amount = safe_amount(cbs_txn.txn_amount)
    dr_cr_flag = (cbs_txn.dr_cr_flag or "").upper().strip()

    if dr_cr_flag == "D":
        return {
            "amount": amount,
            "effect": "DEBIT",
            "is_success": True,
            "is_reversal": False,
        }

    if dr_cr_flag == "C":
        return {
            "amount": amount,
            "effect": "CREDIT",
            "is_success": False,
            "is_reversal": True,
        }

    return {
        "amount": amount,
        "effect": "UNKNOWN",
        "is_success": False,
        "is_reversal": False,
    }


def normalize_switch_transaction(switch_txn):
    """
    Switch:
    Withdrawal + void_code 0 = successful financial transaction
    Withdrawal Reversal = reversed / failed transaction
    """

    if not switch_txn:
        return None

    amount = safe_amount(switch_txn.transaction_amount)
    transaction_type = (switch_txn.transaction_type or "").upper().strip()
    void_code = str(switch_txn.void_code or "").strip()

    if transaction_type == "WITHDRAWAL" and void_code == "0":
        return {
            "amount": amount,
            "effect": "WITHDRAWAL",
            "is_success": True,
            "is_reversal": False,
        }

    if transaction_type == "WITHDRAWAL REVERSAL":
        return {
            "amount": amount,
            "effect": "WITHDRAWAL_REVERSAL",
            "is_success": False,
            "is_reversal": True,
        }

    return {
        "amount": amount,
        "effect": "UNKNOWN",
        "is_success": False,
        "is_reversal": False,
    }


def normalize_ndpg_transaction(ndpg_txn):
    """
    NDPG:
    response_code 00 = successful
    other response codes = failed
    """

    if not ndpg_txn:
        return None

    amount = safe_amount(ndpg_txn.actual_transaction_amount)
    response_code = str(ndpg_txn.response_code or "").strip()

    if response_code == "00":
        return {
            "amount": amount,
            "effect": "SUCCESS",
            "is_success": True,
            "is_reversal": False,
        }

    return {
        "amount": amount,
        "effect": "FAILED",
        "is_success": False,
        "is_reversal": False,
    }