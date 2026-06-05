"""
Validation utilities for the cbs application. These checks protect the database from malformed or duplicate transaction records.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Recon.settings')
django.setup()
from .models import CBSATMTransaction


EXPECTED_RECORD_LENGTH = 203


def validate_cbs_record(parsed_data, raw_line, expected_file_type):
    errors = []

    if len(raw_line) < EXPECTED_RECORD_LENGTH:
        errors.append("Invalid record length")

    if parsed_data.get("file_type") != expected_file_type:
        errors.append(
            f"Wrong file type. Expected {expected_file_type}, found {parsed_data.get('file_type')}"
        )

    if not parsed_data.get("stan_no"):
        errors.append("Missing STAN number")

    if not parsed_data.get("card_no"):
        errors.append("Missing card number")

    if parsed_data.get("dr_cr_flag") not in ["D", "C"]:
        errors.append("Invalid DR/CR flag")

    if not parsed_data.get("txn_date"):
        errors.append("Missing transaction date")

    if not parsed_data.get("txn_time"):
        errors.append("Missing transaction time")

    if not parsed_data.get("atm_id"):
        errors.append("Missing ATM ID")

    if not parsed_data.get("status"):
        errors.append("Missing status code")

    duplicate_exists = CBSATMTransaction.objects.filter(
        stan_no=parsed_data.get("stan_no"),
        card_no=parsed_data.get("card_no"),
        file_type=parsed_data.get("file_type"),
        txn_date=parsed_data.get("txn_date"),
        txn_amount=parsed_data.get("txn_amount"),
    ).exists()

    if duplicate_exists:
        errors.append("Duplicate transaction already exists")

    return errors

