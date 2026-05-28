"""
Service-layer business logic for the cbs application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""


def validate_rgcs_cbs_record(data,decoded_line,expected_file_type):
    """Validate parsed RGCS CBS record.
    Returns list of validation errors.

    Arguments:
        data {dict} -- parsed RGCS CBS record.
        decoded_line {str} -- decoded RGCS CBS record.
        expected_file_type {str} -- expected file type.

    Returns:
        errors {list} -- list of validation errors.
    """

    EXPECTED_RECORD_LENGTH = 203
    errors = []

    allowed_transaction_types = ["44", "45", "46", "49"]
    allowed_account_types = ["10", "20", "30"]

    if len(decoded_line) < EXPECTED_RECORD_LENGTH:
        errors.append("Invalid record length"+" "+ decoded_line)

    if data["transaction_type"] not in allowed_transaction_types:
        errors.append("Invalid transaction type. Allowed values are 44, 45, 46, 49.")

    if not data["stan_no"] or data["stan_no"] == "000000":
        errors.append("Invalid STAN. Zero or blank STAN is not allowed.")

    if not data["card_no"] or set(data["card_no"]) == {"0"}:
        errors.append("Invalid card number. Zero or blank card number is not allowed.")

    if not data["rrn"]:
        errors.append("RRN is required.")

    if data["account_type"] not in allowed_account_types:
        errors.append("Invalid account type. Allowed values are 10, 20, 30.")

    if not data["account_number"] or set(data["account_number"]) == {"0"}:
        errors.append("Invalid account number. Zero or blank account number is not allowed.")

    if data["transaction_flag"] !=expected_file_type:
        errors.append("Invalid transaction type Expected"+{expected_file_type} +"Found :"+ {data["transaction_flag"] })

    if data["dr_cr_flag"] not in ["D", "C"]:
        errors.append("Invalid Dr/Cr flag. Allowed values are D or C.")

    if data["transaction_amount"] <= 0:
        errors.append("Transaction amount must be greater than zero.")

    if not data["terminal_id"]:
        errors.append("Terminal ID is required.")

    if data["response_code"] != "00":
        errors.append("Invalid response code. Only 00 is allowed.")

    return errors