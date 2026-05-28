"""
Service-layer business logic for the ndpg application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal
from datetime import datetime
from io import StringIO
import re

import pandas as pd


ACQUIRER_COLUMNS = [
    "participant_id",
    "transaction_type",
    "from_account_type",
    "to_account_type",
    "transaction_serial_number",
    "response_code",
    "pan_number",
    "approval_no",
    "transaction_date",
    "transaction_time",
    "merchant_category_code",
    "card_acceptor_id",
    "acquirer_id",
    "acquirer_settlement_date",
    "transaction_currency_code",
    "actual_transaction_amount",
    "original_channel",
    "bene_ifsc_code",
    "bene_account_no",
    "rem_ifsc_code",
    "remitter_account_no",
]


ISSUER_COLUMNS = [
    "participant_id",
    "transaction_type",
    "from_account_type",
    "to_account_type",
    "transaction_serial_number",
    "response_code",
    "pan_number",
    "approval_no",
    "transaction_date",
    "transaction_time",
    "merchant_category_code",
    "card_acceptor_settlement_date",
    "card_acceptor_id",
    "acquirer_id",
    "transaction_currency_code",
    "actual_transaction_amount",
    "original_channel",
    "bene_ifsc_code",
    "bene_account_no",
    "rem_ifsc_code",
    "remitter_account_no",
]


def clean_value(value):
    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def parse_file_header(header_line):
    """
    Example:
    16052026_1C
    """

    header_line = header_line.strip()

    match = re.match(r"^(\d{8})_(\d+)[A-Za-z]?$", header_line)

    if not match:
        raise ValueError(
            f"Invalid file header format: {header_line}. "
            "Expected format like 16052026_1C"
        )

    file_date = datetime.strptime(match.group(1), "%d%m%Y").date()
    cycle_no = int(match.group(2))

    return {
        "raw_header": header_line,
        "file_date": file_date,
        "cycle_no": cycle_no,
    }


def parse_eof_line(eof_line):
    """
    Supports:
    EOF131
    EOF 131
    EOF,131
    """

    eof_line = eof_line.strip()

    if not eof_line.upper().startswith("EOF"):
        raise ValueError(
            f"Invalid EOF line: {eof_line}. File must end with EOF."
        )

    numbers = re.findall(r"\d+", eof_line)

    if not numbers:
        return None

    return int(numbers[-1])


def parse_ndpg_date(value):
    value = clean_value(value)

    if not value:
        return None

    value = value.replace(".0", "").strip()

    if re.fullmatch(r"\d{6}", value):
        return datetime.strptime(value, "%y%m%d").date()

    if re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value, "%d%m%Y").date()

    raise ValueError(f"Invalid NDPG date value: {value}")


def parse_ndpg_time(value):
    value = clean_value(value)

    if not value:
        return None

    value = value.replace(".0", "").zfill(6)

    return datetime.strptime(value, "%H%M%S").time()


def parse_amount(value):
    value = clean_value(value)

    if not value:
        return Decimal("0.00")

    value = value.replace(",", "")

    return (Decimal(value) / Decimal("100")).quantize(Decimal("0.01"))


def read_uploaded_lines(uploaded_file):
    """ read lines from uploaded file
    Arguments:
         uploaded_file: uploaded file
    Returns:
        lines (list): list of lines

    """
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")

    lines = [
        line.rstrip("\r\n")
        for line in text.splitlines()
        if line.strip() != ""
    ]

    if len(lines) < 3:
        raise ValueError(
            "Invalid NDPG raw file. File must contain header, data rows and EOF."
        )

    return lines


def get_columns_for_file_type(file_type):
    file_type = (file_type or "").upper().strip()

    if file_type == "ACQUIRER":
        return ACQUIRER_COLUMNS

    if file_type == "ISSUER":
        return ISSUER_COLUMNS

    raise ValueError("Invalid file_type. Expected ACQUIRER or ISSUER.")


def read_raw_rows(data_lines, columns):
    """ Convert , separated line to dataframe
    Arguments:
         data_lines{list}: list of lines
         columns{list}: list of columns
     Returns:
          df {dataframe}: dataframe containing all rows

    Sample row ends with comma, so pandas gets one extra blank column.
    We read without names first, then keep only expected columns.
    """

    csv_content = "\n".join(data_lines)

    df = pd.read_csv(
        StringIO(csv_content),
        dtype=str,
        header=None,
        keep_default_na=False
    )

    expected_count = len(columns)

    if df.shape[1] < expected_count:
        raise ValueError(
            f"Invalid row structure. Expected at least {expected_count} columns, "
            f"found {df.shape[1]} columns."
        )

    # Ignore trailing extra blank column caused by ending comma
    df = df.iloc[:, :expected_count]
    df.columns = columns

    return df


def read_ndpg_imps_raw_file(uploaded_file, file_type):
    """ read IMPS raw flat file from NDPG and converts them to list  dictionary
        Arguments:
            uploaded_file: uploaded file
            file_type: file type
        Returns:
           {
        "header": header_info,
        "eof_record_count": eof_record_count,
        "records": records,
    }
    """

    lines = read_uploaded_lines(uploaded_file)

    file_header_line = lines[0].strip()
    eof_line = lines[-1].strip()

    header_info = parse_file_header(file_header_line)
    eof_record_count = parse_eof_line(eof_line)

    data_lines = lines[1:-1]
    columns = get_columns_for_file_type(file_type)

    df = read_raw_rows(data_lines, columns)

    parsed_count = len(df)

    if eof_record_count is not None and eof_record_count != parsed_count:
        raise ValueError(
            f"EOF record count mismatch. EOF says {eof_record_count}, "
            f"but parsed records are {parsed_count}."
        )

    records = []

    for _, row in df.iterrows():
        transaction_serial_number = clean_value(
            row.get("transaction_serial_number")
        )

        if not transaction_serial_number:
            continue

        if file_type.upper() == "ACQUIRER":
            settlement_date = parse_ndpg_date(
                row.get("acquirer_settlement_date")
            )
        else:
            settlement_date = parse_ndpg_date(
                row.get("card_acceptor_settlement_date")
            )

        records.append({
            "participant_id": clean_value(row.get("participant_id")),
            "transaction_type": clean_value(row.get("transaction_type")),
            "from_account_type": clean_value(row.get("from_account_type")),
            "to_account_type": clean_value(row.get("to_account_type")),
            "transaction_serial_number": transaction_serial_number,
            "response_code": clean_value(row.get("response_code")),
            "pan_number": clean_value(row.get("pan_number")),
            "approval_no": clean_value(row.get("approval_no")),
            "transaction_date": parse_ndpg_date(row.get("transaction_date")),
            "transaction_time": parse_ndpg_time(row.get("transaction_time")),
            "merchant_category_code": clean_value(
                row.get("merchant_category_code")
            ),
            "card_acceptor_settlement_date": (
                settlement_date or header_info["file_date"]
            ),
            "card_acceptor_id": clean_value(row.get("card_acceptor_id")),
            "acquirer_id": clean_value(row.get("acquirer_id")),
            "transaction_currency_code": clean_value(
                row.get("transaction_currency_code")
            ),
            "actual_transaction_amount": parse_amount(
                row.get("actual_transaction_amount")
            ),
            "original_channel": clean_value(row.get("original_channel")),
            "bene_ifsc_code": clean_value(row.get("bene_ifsc_code")),
            "bene_account_no": clean_value(row.get("bene_account_no")),
            "rem_ifsc_code": clean_value(row.get("rem_ifsc_code")),
            "remitter_account_no": clean_value(row.get("remitter_account_no")),
        })

    return {
        "header": header_info,
        "eof_record_count": eof_record_count,
        "records": records,
    }