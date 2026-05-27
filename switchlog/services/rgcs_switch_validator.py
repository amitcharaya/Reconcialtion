"""
Service-layer business logic for the switchlog application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from switchlog.models import RGCSSwitchUploadBatch


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


def validate_rgcs_switch_columns(columns):
    errors = []

    for column in REQUIRED_COLUMNS:
        if column not in columns:
            errors.append(f"Missing required column: {column}")

    return errors


def validate_rgcs_switch_record(record, row_number):
    errors = []

    required_fields = [
        "tranx_datetime",
        "stan_no",
        "rrn",
        "txn_type",
        "amount_req",
        "amount_approved",
        "interface_type",
        "void_code",
        "status",
    ]

    for field in required_fields:
        if record.get(field) in [None, ""]:
            errors.append(f"Row {row_number}: Missing {field}")

    if record.get("rrn") and len(str(record["rrn"])) < 6:
        errors.append(f"Row {row_number}: Invalid RRN")

    if record.get("stan_no") and len(str(record["stan_no"])) > 20:
        errors.append(f"Row {row_number}: Invalid STAN number")

    return errors


def check_duplicate_rgcs_switch_file(source_filename):
    return RGCSSwitchUploadBatch.objects.filter(
        source_filename=source_filename
    ).exists()