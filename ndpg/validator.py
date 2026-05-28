import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reconcilation.settings')
django.setup()

from .models import NDPGATMTransaction


def validate_ndpg_record(parsed_data, raw_line, expected_file_type):
    """
    Validation utilities for the ndpg application. These checks protect the database from malformed or duplicate transaction records.


    """

    errors = []

    if len(raw_line) < 260:
        errors.append("Record too short")

    if parsed_data.get("file_type") != expected_file_type:
        errors.append("Wrong file type")

    if not parsed_data.get("stan_no"):
        errors.append("Missing STAN")

    if not parsed_data.get("transaction_serial_number"):
        errors.append("Missing Transaction Serial Number")

    if not parsed_data.get("transaction_date"):
        errors.append("Missing Transaction Date")

    if parsed_data.get("transaction_amount") is None:
        errors.append("Invalid Transaction Amount")

    duplicate_exists = NDPGATMTransaction.objects.filter(
        file_type=parsed_data.get("file_type"),
        cycle_no=parsed_data.get("cycle_no"),
        stan_no=parsed_data.get("stan_no"),
        transaction_date=parsed_data.get("transaction_date"),
        transaction_amount=parsed_data.get("transaction_amount"),
    ).exists()

    if duplicate_exists:
        errors.append("Duplicate transaction")

    return errors
