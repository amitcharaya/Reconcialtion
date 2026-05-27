"""
Service-layer business logic for the ndpg application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from ndpg.models import RGCSRawTransaction


def validate_rgcs_record(record, line_number, source_filename):
    errors = []

    required_fields = [
        "message_type",
        "product_id",
        "transaction_type",
        "action_code",
        "response_code",
        "pan_number",
        "rrn",
        "transaction_date",
        "transaction_time",
        "transaction_amount",
    ]

    for field in required_fields:
        if not record.get(field):
            errors.append(
                f"{source_filename} line {line_number}: Missing {field}"
            )

    if record.get("product_id") not in ["ATM", "POS"]:
        errors.append(
            f"{source_filename} line {line_number}: Invalid product_id {record.get('product_id')}"
        )

    if record.get("action_code") not in ["A", "D", "R"]:
        errors.append(
            f"{source_filename} line {line_number}: Invalid action_code {record.get('action_code')}"
        )

    if record.get("rrn") and len(record["rrn"]) != 12:
        errors.append(
            f"{source_filename} line {line_number}: RRN must be 12 characters"
        )

    return errors


def validate_trailer(parsed_file, source_filename):
    errors = []

    trailer = parsed_file.get("trailer")
    records = parsed_file.get("records", [])

    if trailer:
        trailer_count = trailer.get("number_of_records")

        if trailer_count != len(records):
            errors.append(
                f"{source_filename}: Trailer record count {trailer_count} does not match parsed records {len(records)}"
            )

    return errors


def check_duplicate_file(source_filename):
    return RGCSRawTransaction.objects.filter(
        source_filename=source_filename
    ).exists()