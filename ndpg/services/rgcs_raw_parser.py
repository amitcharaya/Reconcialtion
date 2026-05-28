"""
Service-layer business logic for the ndpg application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from datetime import datetime
from decimal import Decimal


RGCS_RECORD_LENGTH = 419


RGCS_FIELDS = [
    ("message_type", 2),
    ("product_id", 3),
    ("transaction_type", 2),
    ("from_account_type", 2),
    ("to_account_type", 2),
    ("action_code", 1),
    ("response_code", 2),
    ("pan_number", 19),
    ("approval_number", 6),
    ("rrn", 12),
    ("transaction_date_raw", 7),
    ("transaction_time_raw", 6),
    ("merchant_category_code", 4),
    ("card_acceptor_id", 15),
    ("terminal_id", 8),
    ("terminal_location", 40),
    ("acquirer_id", 11),
    ("transaction_currency_code", 3),
    ("transaction_amount_raw", 15),
    ("card_holder_billing_currency", 3),
    ("card_holder_billing_amount_raw", 15),
    ("pan_entry_mode", 2),
    ("pin_entry_capability", 1),
    ("pos_condition_code", 2),
    ("acquirer_country_code", 3),
    ("additional_amount", 15),
    ("rupay_product", 5),
    ("cvd2_match_result", 1),
    ("cvd_icvd_match_result", 1),
    ("recurring_payment_indicator", 2),
    ("eci_indicator", 2),
    ("ics1_result_code", 2),
    ("fraud_score", 5),
    ("emi_amount", 26),
    ("arqc_authorization", 1),
    ("transaction_id", 30),
    ("loyalty_point", 6),
    ("ics2_result_code", 1),
    ("customer_mobile_number", 12),
    ("image_code", 5),
    ("personal_phase", 5),
    ("uid_number", 12),
    ("card_data_input_capability", 1),
    ("cardholder_auth_capability", 1),
    ("card_capture_capability", 1),
    ("terminal_operating_environment", 1),
    ("cardholder_present_data", 1),
    ("card_present_data", 1),
    ("card_data_input_mode", 1),
    ("cardholder_auth_mode", 1),
    ("cardholder_auth_entity", 1),
    ("card_data_output_capability", 1),
    ("terminal_data_output_capability", 1),
    ("pin_capture_capability", 1),
    ("zip_code", 9),
    ("advice_reason_code", 7),
    ("it_pan", 10),
    ("intr_auth_nw", 15),
    ("otp_indicator", 1),
    ("ics_txn_id", 15),
    ("nw_data", 12),
    ("service_code", 3),
    ("actual_txn_currency_code", 3),
    ("actual_txn_amount_raw", 15),
]


def clean_value(value):
    value = value.strip()
    return value if value else None


def parse_amount(value):
    value = value.strip()

    if not value:
        return Decimal("0.00")

    if not value.isdigit():
        return Decimal("0.00")

    return Decimal(value) / Decimal("100")


def parse_rgcs_date(value):
    """
    RGCS sample has 7-character date field like:
    1260401

    First character may be filler. Last 6 digits are YYMMDD.
    """
    value = value.strip()

    if len(value) == 7:
        value = value[-6:]

    return datetime.strptime(value, "%y%m%d").date()


def parse_rgcs_time(value):
    return datetime.strptime(value.strip(), "%H%M%S").time()


def parse_header(line):
    return {
        "header_identifier": line[0:3],
        "file_generated_datetime_raw": line[3:15],
        "settlement_date_raw": line[15:21],
        "participant_id": line[21:32],
        "file_category": line[32:33],
        "version_number": line[33:38],
    }


def parse_trailer(line):
    """ parse header from raw file and convert ito dict containing fields
        Arguments:
              line{str} -- fixed length line
        Returns:
            return {
        "trailer_identifier": line[0:3],
        "number_of_records": int(line[3:11]),
        "run_total_amount": parse_amount(line[11:26]),
    }

    """
    return {
        "trailer_identifier": line[0:3],
        "number_of_records": int(line[3:11]),
        "run_total_amount": parse_amount(line[11:26]),
    }


def parse_data_record(line):
    """ parse fixed length file to dictionary object for RGCS Raw file convert to dict
        Arguments:
              line{str} -- fixed length line
        Returns:
              parsed {dict} -- dictionary object for RGCS Raw file

    """
    if len(line) != RGCS_RECORD_LENGTH:
        raise ValueError(
            f"Invalid RGCS record length. Expected {RGCS_RECORD_LENGTH}, got {len(line)}"
        )

    data = {}
    start = 0

    for field_name, length in RGCS_FIELDS:
        end = start + length
        data[field_name] = line[start:end]
        start = end

    txn_date = parse_rgcs_date(data["transaction_date_raw"])
    txn_time = parse_rgcs_time(data["transaction_time_raw"])
    txn_datetime = datetime.combine(txn_date, txn_time)

    parsed = {
        "message_type": clean_value(data["message_type"]),
        "product_id": clean_value(data["product_id"]),
        "transaction_type": clean_value(data["transaction_type"]),
        "from_account_type": clean_value(data["from_account_type"]),
        "to_account_type": clean_value(data["to_account_type"]),
        "action_code": clean_value(data["action_code"]),
        "response_code": clean_value(data["response_code"]),
        "pan_number": clean_value(data["pan_number"]),
        "approval_number": clean_value(data["approval_number"]),
        "rrn": clean_value(data["rrn"]),
        "stan_no": clean_value(data["rrn"][-6:]) if data["rrn"] else None,
        "transaction_date": txn_date,
        "transaction_time": txn_time,
        "transaction_datetime": txn_datetime,
        "merchant_category_code": clean_value(data["merchant_category_code"]),
        "card_acceptor_id": clean_value(data["card_acceptor_id"]),
        "terminal_id": clean_value(data["terminal_id"]),
        "terminal_location": clean_value(data["terminal_location"]),
        "acquirer_id": clean_value(data["acquirer_id"]),
        "transaction_currency_code": clean_value(data["transaction_currency_code"]),
        "transaction_amount": parse_amount(data["transaction_amount_raw"]),
        "card_holder_billing_currency": clean_value(data["card_holder_billing_currency"]),
        "card_holder_billing_amount": parse_amount(data["card_holder_billing_amount_raw"]),
        "actual_txn_currency_code": clean_value(data["actual_txn_currency_code"]),
        "actual_txn_amount": parse_amount(data["actual_txn_amount_raw"]),
        "raw_data": {key: clean_value(value) for key, value in data.items()},
    }

    return parsed


def parse_rgcs_file(uploaded_file):
    """
    Returns:
    {
        "header": dict or None,
        "trailer": dict or None,
        "records": list[dict],
    }
    """

    content = uploaded_file.read().decode("utf-8", errors="ignore")
    lines = [line.rstrip("\r\n") for line in content.splitlines() if line.strip()]

    header = None
    trailer = None
    records = []

    for line in lines:
        if line.startswith("HDR"):
            header = parse_header(line)
        elif line.startswith("TRL"):
            trailer = parse_trailer(line)
        else:
            records.append(parse_data_record(line))

    return {
        "header": header,
        "trailer": trailer,
        "records": records,
    }