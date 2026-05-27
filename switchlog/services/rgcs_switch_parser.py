"""
Service-layer business logic for the switchlog application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

import pandas as pd
from decimal import Decimal
from datetime import datetime


REQUIRED_COLUMNS = [
    "SN",
    "TRANX DATE",
    "TERMINAL ID",
    "TERMINAL TYPE",
    "STAN NO",
    "CARD NO.",
    "ACCOUNT TYPE",
    "ACCOUNT NO.",
    "ACQ.BANK",
    "RET REF NO.",
    "TXN.TYPE",
    "AMOUNT REQ.",
    "AMOUNT APPROVED",
    "INTF. TYPE",
    "VOID CODE",
    "STATUS",
]


def clean_value(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value else None


def clean_decimal(value):
    if pd.isna(value) or value == "":
        return Decimal("0.00")
    return Decimal(str(value).replace(",", "").strip())


def parse_datetime_value(value):
    if pd.isna(value):
        raise ValueError("TRANX DATE is blank")

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)

    value = str(value).strip()

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    raise ValueError(f"Invalid TRANX DATE format: {value}")


def normalize_columns(df):
    df.columns = [str(col).strip() for col in df.columns]
    return df


def parse_rgcs_switch_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df = normalize_columns(df)

    records = []

    for index, row in df.iterrows():
        if row.isna().all():
            continue

        tranx_datetime = parse_datetime_value(row.get("TRANX DATE"))

        record = {
            "serial_no": int(row["SN"]) if not pd.isna(row.get("SN")) else None,
            "tranx_datetime": tranx_datetime,
            "tranx_date": tranx_datetime.date(),
            "tranx_time": tranx_datetime.time(),

            "terminal_id": clean_value(row.get("TERMINAL ID")),
            "terminal_type": clean_value(row.get("TERMINAL TYPE")),
            "switch": clean_value(row.get("SWITCH")),

            "stan_no": clean_value(row.get("STAN NO")),
            "card_no": clean_value(row.get("CARD NO.")),

            "account_type": clean_value(row.get("ACCOUNT TYPE")),
            "account_no": clean_value(row.get("ACCOUNT NO.")),

            "acq_bank": clean_value(row.get("ACQ.BANK")),
            "rrn": clean_value(row.get("RET REF NO.")),

            "mcc": clean_value(row.get("MCC")),
            "txn_type": clean_value(row.get("TXN.TYPE")),
            "con_txn": clean_value(row.get("CON.TXN.")),

            "amount_req": clean_decimal(row.get("AMOUNT REQ.")),
            "amount_approved": clean_decimal(row.get("AMOUNT APPROVED")),

            "interface_type": clean_value(row.get("INTF. TYPE")),
            "void_code": clean_value(row.get("VOID CODE")),

            "atm_location": clean_value(row.get("ATM LOCATION")),
            "embossed_name": clean_value(row.get("EMBOSSED NAME")),

            "status": clean_value(row.get("STATUS")),
            "error": clean_value(row.get("ERROR")),

            "raw_data": {
                str(col): clean_value(row.get(col))
                for col in df.columns
            },
        }

        records.append(record)

    return {
        "columns": list(df.columns),
        "records": records,
    }