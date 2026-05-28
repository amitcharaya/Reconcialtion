"""
Contains helper function to upload CBS RGCS files


"""

from decimal import Decimal
from datetime import datetime


EXPECTED_RGCS_CBS_RECORD_LENGTH = 215


def parse_rgcs_cbs_record(line):
    """
    Parse one fixed-width RGCS CBS record.
    Position mapping is based on RGCS CBS Recon File Specification.
    Python slicing is zero-based, while specification positions are one-based.

    Arguments:
        line {string} -- line to parse
        data {dictionary} -- dictionary containing field for CBS RGCS Transaction

        transaction_type {string} -- type of transaction
        stan_no {string} -- stan number for transaction
        card_no {string} -- card number for transaction
        rrn {string} -- rrn for transaction
        account_type {string} -- account type for transaction
        account_number {string} -- account number for transaction
        account_holder_name {string} -- account holder name for transaction
        branch_code {string} -- branch_code for transaction
        branch_name {string} -- branch_name for transaction
        transaction_flag {string} -- transaction flag for transaction
        dr_cr_flag {string} -- dr cr flag for transaction
        transaction_amount {Decimal} -- transaction amount for transaction
        transaction_date {datetime} -- transaction date for transaction
        transaction_time {datetime} -- transaction time for transaction
        value_date {datetime} -- value date for transaction
        value_time {datetime} -- value time for transaction
        acquirer_institution_code {string} -- acquirer institution code for transaction
        terminal_id {string} -- terminal id for transaction
        terminal_location {string} -- terminal location for transaction
        response_code {string} -- response code for transaction
        raw_record {string} -- raw record for transaction

    """

    raw_record = line.rstrip("\r\n")

    if not raw_record.strip():
        return None

    if len(raw_record) != EXPECTED_RGCS_CBS_RECORD_LENGTH:
        raise ValueError(
            f"Invalid record length. Expected 215 characters, found {len(raw_record)}"
        )

    amount_raw = raw_record[116:131].strip()

    if not amount_raw:
        amount = Decimal("0.00")
    else:
        amount = Decimal(amount_raw) / Decimal("100")

    data = {
        "transaction_type": raw_record[0:2].strip(),
        "stan_no": raw_record[2:8].strip(),
        "card_no": raw_record[8:27].strip(),
        "rrn": raw_record[27:39].strip(),
        "account_type": raw_record[39:41].strip(),
        "account_number": raw_record[41:59].strip(),
        "account_holder_name": raw_record[59:85].strip(),
        "branch_code": raw_record[85:89].strip(),
        "branch_name": raw_record[89:114].strip(),
        "transaction_flag": raw_record[114:115].strip(),
        "dr_cr_flag": raw_record[115:116].strip(),
        "transaction_amount": amount,
        "transaction_date": datetime.strptime(raw_record[131:139], "%Y%m%d").date(),
        "transaction_time": datetime.strptime(raw_record[139:145], "%H%M%S").time(),
        "value_date": datetime.strptime(raw_record[145:153], "%Y%m%d").date(),
        "value_time": datetime.strptime(raw_record[153:159], "%H%M%S").time(),
        "acquirer_institution_code": raw_record[159:165].strip(),
        "terminal_id": raw_record[165:173].strip(),
        "terminal_location": raw_record[173:213].strip(),
        "response_code": raw_record[213:215].strip(),
        "raw_record": raw_record,

    }

    return data