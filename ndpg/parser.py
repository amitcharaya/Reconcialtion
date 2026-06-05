import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Recon.settings')
django.setup()

from decimal import Decimal
from reconciliation.utils import normalize_date

def parse_decimal(value):
    """ Convert paise to RS.
    Arguments:
        value {number} -- paise
    Returns:
          RS -- decimal value Paise to RS Conversion

    """
    value = value.strip()

    if not value:
        return None

    if not value.isdigit():
        raise ValueError(f"Invalid numeric value: {value}")

    return Decimal(value) / Decimal("100")

def parse_ndpg_acquirer_record(line, cycle_no):
    """ parse NDPG acquirer flat file for ATM  Transactions and convert them to dict from flat line

        Arguments:
            line {str} -- ndpg_acquirer_record line
            cycle_no {int} -- cycle_no from ndpg_acquirer_record
        Returns:
            dict -- dict from ndpg_acquirer_record fields
    """
    return {
        "file_type": "ACQUIRER",
        "cycle_no": cycle_no,

        "participant_id": line[0:3].strip(),
        "transaction_type": line[3:5].strip(),
        "from_account_type": line[5:7].strip(),
        "to_account_type": line[7:9].strip(),

        "transaction_serial_number": line[9:21].strip(),
        "response_code": line[21:23].strip(),
        "pan_number": line[23:39].strip(),

        "member_number": line[43:49].strip(),
        "approval_number": line[49:55].strip(),
        "stan_no": line[55:61].strip(),

        "transaction_date": normalize_date(line[61:67].strip()),
        "transaction_time": line[67:73].strip(),

        "merchant_category_code": line[73:77].strip(),
        "card_acceptor_settlement_date": normalize_date(line[77:83].strip()),
        "card_acceptor_id": line[83:98].strip(),
        "card_acceptor_terminal_id": line[98:106].strip(),
        "card_acceptor_terminal_location": line[106:142].strip(),

        "acquirer_id": line[142:157].strip(),
        "acquirer_settlement_date": normalize_date(line[157:163].strip()),

        "transaction_currency_code": line[163:166].strip(),

        "transaction_amount": parse_decimal(line[166:181]),
        "actual_transaction_amount": parse_decimal(line[181:196]),
        "transaction_activity_fee": parse_decimal(line[196:211]),

        "raw_record": line,
    }

def parse_ndpg_issuer_record(line, cycle_no):
    """ parse NDPG Issuer flat file for ATM  Transactions and convert them to dict from flat line

            Arguments:
                line {str} -- ndpg_acquirer_record line
                cycle_no {int} -- cycle_no from ndpg_acquirer_record
            Returns:
                dict -- dict from ndpg_acquirer_record fields
        """
    return {
        "file_type": "ISSUER",
        "cycle_no": cycle_no,

        "participant_id": line[0:3].strip(),
        "transaction_type": line[3:5].strip(),
        "from_account_type": line[5:7].strip(),
        "to_account_type": line[7:9].strip(),

        "transaction_serial_number": line[9:21].strip(),
        "response_code": line[21:23].strip(),
        "pan_number": line[23:39].strip(),

        "member_number": line[43:49].strip(),
        "approval_number": line[49:55].strip(),
        "stan_no": line[55:61].strip(),

        "transaction_date": normalize_date(line[61:67].strip()),
        "transaction_time": line[67:73].strip(),

        "merchant_category_code": line[73:77].strip(),
        "card_acceptor_settlement_date": normalize_date(line[77:83].strip()),
        "card_acceptor_id": line[83:98].strip(),
        "card_acceptor_terminal_id": line[98:106].strip(),
        "card_acceptor_terminal_location": line[106:142].strip(),

        "acquirer_id": line[142:157].strip(),
        "network_id": line[157:160].strip(),

        "account_1_number": line[160:176].strip(),
        "account_1_branch_id": line[176:189].strip(),

        "account_2_number": line[189:205].strip(),
        "account_2_branch_id": line[205:218].strip(),

        "transaction_currency_code": line[218:221].strip(),

        "transaction_amount": parse_decimal(line[221:236]),
        "actual_transaction_amount": parse_decimal(line[236:251]),
        "transaction_activity_fee": parse_decimal(line[251:266]),

        "raw_record": line,
    }

