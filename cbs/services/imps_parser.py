"""
Service-layer business logic for the cbs application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal
from datetime import datetime
import re


EXPECTED_LENGTH = 250


def clean(value):
    return value.strip()


def parse_amount(value):
    value = clean(value)

    if not value.isdigit():
        raise ValueError(f"Invalid transaction amount: {value}")

    return (Decimal(value) / Decimal("100")).quantize(Decimal("0.01"))


def parse_date(value, field_name):
    value = clean(value)

    try:
        return datetime.strptime(value, "%y%m%d").date()
    except ValueError:
        raise ValueError(f"Invalid {field_name}: {value}. Expected YYMMDD.")


def parse_time(value, field_name):
    value = clean(value)

    try:
        return datetime.strptime(value, "%H%M%S").time()
    except ValueError:
        raise ValueError(f"Invalid {field_name}: {value}. Expected HHMMSS.")


def validate_digits(value, field_name, length=None, allow_zero=True):
    value = clean(value)

    if length and len(value) != length:

        raise ValueError(f"{field_name} must be {length} digits.")

    if not value.isdigit():
        raise ValueError(f"{field_name} must contain only digits.")

    if not allow_zero and int(value) == 0:
        raise ValueError(f"{field_name} cannot be zero.")

    return value


def validate_name(value, field_name):
    value = value.rstrip()

    if not value:
        raise ValueError(f"{field_name} cannot be blank.")

    """
    if not re.match(r"^[A-Za-z0-9 ]+$", value):
        raise ValueError(f"{field_name} contains special characters.")

    return value
"""

def parse_cbs_imps_record(line, expected_file_type):

    """Parse cbs imps record

    Arguments:
        line {str} -- cbs imps record
        expected_file_type {str} -- expected file type
    Returns:
        parsed {dict} -- parsed cbs imps record
    """
    line = line.rstrip("\n\r")

    if len(line) < EXPECTED_LENGTH:
        raise ValueError(
            f"Invalid record length {len(line)}. Expected at least {EXPECTED_LENGTH}."
        )

    data = {
        "transaction_serial_number": line[0:12],
        "account_type": line[12:14],
        "account_number": line[14:32],
        "account_holder_name": line[32:58],
        "branch_code": line[58:62],
        "branch_name": line[62:87],
        "nbin": line[87:91],
        "mobile_number": line[91:101],
        "ifsc": line[101:112],
        "aadhaar_number": line[112:124],
        "transaction_type": line[124:125],
        "dr_cr_flag": line[125:126],
        "transaction_amount": line[126:141],
        "transaction_code": line[141:143],
        "rem_bene_nbin": line[143:147],
        "rem_bene_mobile_number": line[147:157],
        "rem_bene_ifsc": line[157:168],
        "rem_bene_account_number": line[168:186],
        "rem_bene_aadhaar_number": line[186:198],
        "transaction_date": line[198:204],
        "transaction_time": line[204:210],
        "value_date": line[210:216],
        "value_time": line[216:222],
        "original_channel": line[222:225],
        "atm_id": line[225:233],
        "remark": line[233:248],
        "response_code": line[248:250],
    }

    if data["account_type"] not in ["10", "20", "30"]:
        raise ValueError("Account Type must be 10, 20, or 30.")

    if data["transaction_type"] not in ["I", "A", "O"]:
        raise ValueError("Transaction Type must be I, A, or O.")

    if data["transaction_type"] != expected_file_type:
        raise ValueError(
            f"File type mismatch. Expected {expected_file_type}, "
            f"found {data['transaction_type']}."
        )

    if data["dr_cr_flag"] not in ["D", "C"]:
        raise ValueError("DR/CR Flag must be D or C.")

    if data["response_code"] != "00":
        raise ValueError("Response Code must be 00.")

    parsed = {

        "transaction_serial_number": validate_digits(
            data["transaction_serial_number"],
            "Transaction Serial Number",
            12,
        ),
        "account_type": data["account_type"],

        "account_holder_name": validate_name(
            data["account_holder_name"],
            "Account Holder Name",
        ),
        "branch_code": validate_digits(
            data["branch_code"],
            "Branch Code",
            4,
        ),
        "branch_name": data["branch_name"].rstrip(),
        "nbin": validate_digits(
            data["nbin"],
            "NBIN",
            4,
            allow_zero=False,
        ),
        "mobile_number": data["mobile_number"].strip(),
        "ifsc": data["ifsc"].strip(),
        "aadhaar_number": data["aadhaar_number"].strip(),
        "transaction_type": data["transaction_type"],
        "dr_cr_flag": data["dr_cr_flag"],
        "transaction_amount": parse_amount(data["transaction_amount"]),
        "transaction_code": validate_digits(
            data["transaction_code"],
            "Transaction Code",
            2,
            allow_zero=False,
        ),
        "rem_bene_nbin": validate_digits(
            data["rem_bene_nbin"],
            "Remitter/Beneficiary NBIN",
            4,
            allow_zero=False,
        ),
        "rem_bene_mobile_number": data["rem_bene_mobile_number"].strip(),
        "rem_bene_ifsc": data["rem_bene_ifsc"].strip(),
        "rem_bene_account_number": data["rem_bene_account_number"].strip(),
        "rem_bene_aadhaar_number": data["rem_bene_aadhaar_number"].strip(),
        "transaction_date": parse_date(
            data["transaction_date"],
            "Transaction Date",
        ),
        "transaction_time": parse_time(
            data["transaction_time"],
            "Transaction Time",
        ),
        "value_date": parse_date(data["value_date"], "Value Date"),
        "value_time": parse_time(data["value_time"], "Value Time"),
        "original_channel": data["original_channel"].strip(),
        "atm_id": data["atm_id"].strip(),
        "remark": data["remark"].strip(),
        "response_code": data["response_code"],
        "raw_data": line,
    }

    if not parsed["branch_name"]:
        raise ValueError("Branch Name cannot be blank.")

    if not parsed["original_channel"]:
        raise ValueError("Original Channel cannot be blank.")

    return parsed