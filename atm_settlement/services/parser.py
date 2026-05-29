import os
import re
import pandas as pd
from decimal import Decimal
from datetime import datetime


def to_decimal(value):
    try:
        if value is None:
            return Decimal("0.000")

        value = str(value).replace(",", "").strip()

        if value == "" or value.lower() == "nan":
            return Decimal("0.000")

        return Decimal(value)
    except Exception:
        return Decimal("0.000")


def to_int(value):
    try:
        if value is None:
            return 0

        value = str(value).replace(",", "").strip()

        if value == "" or value.lower() == "nan":
            return 0

        return int(float(value))
    except Exception:
        return 0


def validate_atm_ntsl_filename(filename):
    """
    Expected filename:
    NTSLPSCDDMMYY_1C.xls

    Example:
    NTSLPSC280526_1C.xls
    """

    base_name = os.path.basename(filename)

    pattern = r"^NTSLPSC(\d{6})_(\d+C)\.xls$"
    match = re.match(pattern, base_name, re.IGNORECASE)

    if not match:
        raise ValueError("Invalid ATM NTSL file name. Expected format: NTSLPSCDDMMYY_1C.xls")

    date_str = match.group(1)
    cycle_no = match.group(2).upper()

    settlement_date = datetime.strptime(date_str, "%d%m%y").date()

    return settlement_date, cycle_no


def parse_atm_ntsl_file(file_path):
    """
    ATM NTSL file is actually HTML table saved with .xls extension.
    Therefore we use pandas.read_html instead of read_excel.
    """

    tables = pd.read_html(file_path)

    main_table = None

    for table in tables:
        if table.shape[1] >= 4:
            first_col_values = table.iloc[:, 0].astype(str).str.lower().tolist()
            if any("acquirer" in value or "issuer" in value for value in first_col_values):
                main_table = table
                break

    if main_table is None:
        raise ValueError("Could not find ATM settlement table in file.")

    items = []

    issuer_sub_total = Decimal("0.000")
    acquirer_sub_total = Decimal("0.000")
    settlement_amount = Decimal("0.000")
    net_adjusted_amount = Decimal("0.000")
    final_settlement_amount = Decimal("0.000")

    for _, row in main_table.iterrows():
        description = row.iloc[0]

        if pd.isna(description):
            continue

        description = str(description).strip()

        if description == "" or description.lower() == "nan":
            continue

        txn_count = to_int(row.iloc[1]) if len(row) > 1 else 0
        debit_amount = to_decimal(row.iloc[2]) if len(row) > 2 else Decimal("0.000")
        credit_amount = to_decimal(row.iloc[3]) if len(row) > 3 else Decimal("0.000")

        clean_desc = description.lower().replace(" ", "")

        if "issuer/acquirersubtotals" in clean_desc:
            issuer_sub_total = debit_amount
            acquirer_sub_total = credit_amount
            continue

        if "settlementamount" in clean_desc:
            settlement_amount = credit_amount if credit_amount != 0 else debit_amount
            continue

        if "netadjustedamount" in clean_desc:
            net_adjusted_amount = credit_amount if credit_amount != 0 else debit_amount
            continue

        if "finalsettlementamount" in clean_desc:
            final_settlement_amount = credit_amount if credit_amount != 0 else debit_amount
            continue

        items.append({
            "description": description,
            "txn_count": txn_count,
            "debit_amount": debit_amount,
            "credit_amount": credit_amount,
        })

    return {
        "items": items,
        "issuer_sub_total": issuer_sub_total,
        "acquirer_sub_total": acquirer_sub_total,
        "settlement_amount": settlement_amount,
        "net_adjusted_amount": net_adjusted_amount,
        "final_settlement_amount": final_settlement_amount,
    }


def get_amount(items, description):
    for item in items:
        if item.description.lower().strip() == description.lower().strip():
            return item
    return None