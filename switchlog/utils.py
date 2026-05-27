"""
Python module used by the switchlog application.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd


COLUMN_MAP = {
    "Transaction Date": "transaction_datetime",
    "Transaction Id": "transaction_id",
    "Transaction Category": "transaction_category",
    "Transaction Type": "transaction_type",
    "Transaction Particulars": "transaction_particulars",
    "Debit Amount": "debit_amount",
    "Credit Amount": "credit_amount",
    "Status": "status",
    "RRN No.": "rrn",
    "Rem MMID": "rem_mmid",
    "Rem Account": "rem_account",
    "Remitter Name": "remitter_name",
    "Rem Mobile": "rem_mobile",
    "Bene MAS": "bene_mas",
    "Bene NBIN": "bene_nbin",
    "Bene Mobile": "bene_mobile",
    "Bene Account": "bene_account",
    "Beneficiary Name": "beneficiary_name",
    "Bene IFSC": "beneficiary_ifsc",
    "Product Indicator": "product_indicator",
    "Original Channel": "original_channel",
    "CBS Status": "cbs_status",
    "CBS RC": "cbs_rc",
    "CBS Reversal Status": "cbs_reversal_status",
    "CBS Reverasal RC": "cbs_reversal_rc",
    "NFS Status": "nfs_status",
    "NFS Verification Status": "nfs_verification_status",
    "NFS Verification RC": "nfs_verification_rc",
    "IMPS RC": "imps_rc",
    "Remark": "remark",
    "Description": "description",
}


REQUIRED_FIELDS = [
    "transaction_datetime",
    "transaction_id",
    "rrn",
    "transaction_type",
    "status",
]


def clean_value(value):
    if pd.isna(value):
        return None
    return str(value).strip()


def parse_decimal(value):
    if pd.isna(value) or value in ["", None]:
        return Decimal("0.00")

    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return Decimal("0.00")


def parse_datetime(value):
    if pd.isna(value) or value in ["", None]:
        raise ValueError("Transaction Date is empty")

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)

    value = str(value).strip()

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Invalid transaction date format: {value}")


def get_transaction_amount(debit_amount, credit_amount):
    debit = parse_decimal(debit_amount)
    credit = parse_decimal(credit_amount)

    if debit > 0:
        return debit

    if credit > 0:
        return credit

    return Decimal("0.00")