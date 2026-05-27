"""
Service-layer business logic for the cbs application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import transaction

from cbs.models import CBSIMPSUploadBatch, CBSIMPSTransaction
from cbs.services.imps_parser import parse_cbs_imps_record


def read_file_lines(uploaded_file):
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")

    return [
        line for line in text.splitlines()
        if line.strip()
    ]


def parse_file_records(uploaded_file, file_type):
    lines = read_file_lines(uploaded_file)

    if not lines:
        raise ValueError(f"{uploaded_file.name} is empty.")

    parsed_records = []

    for index, line in enumerate(lines, start=1):
        try:
            parsed = parse_cbs_imps_record(
                line=line,
                expected_file_type=file_type
            )

            parsed_records.append(parsed)

        except Exception as exc:
            raise ValueError(
                f"{uploaded_file.name} line {index}: {exc}"
            )

    return parsed_records


def import_cbs_imps_files(acquirer_file, issuer_file, onus_file):
    acquirer_records = parse_file_records(acquirer_file, "A")
    issuer_records = parse_file_records(issuer_file, "I")
    onus_records = parse_file_records(onus_file, "O")

    all_records = (
        acquirer_records
        + issuer_records
        + onus_records
    )

    if not all_records:
        raise ValueError("No valid CBS IMPS records found.")

    batch_date = all_records[0]["transaction_date"]

    for record in all_records:
        if record["transaction_date"] != batch_date:
            raise ValueError(
                "All three CBS IMPS files must belong to the same transaction date."
            )

    duplicate_exists = CBSIMPSUploadBatch.objects.filter(
        batch_date=batch_date,

        upload_status="SUCCESS",
    ).exists()

    if duplicate_exists:
        raise ValueError(
            "Duplicate upload blocked. These CBS IMPS files were already uploaded."
        )

    with transaction.atomic():
        batch = CBSIMPSUploadBatch.objects.create(
            batch_date=batch_date,
            acquirer_filename=acquirer_file.name,
            issuer_filename=issuer_file.name,
            onus_filename=onus_file.name,
            upload_status="FAILED",
            total_records=0,
            total_errors=0,
        )

        total_records = 0
        total_errors = 0
        errors = []

        for record in all_records:
            try:
                CBSIMPSTransaction.objects.update_or_create(
                    transaction_serial_number=record["transaction_serial_number"],
                    transaction_date=record["transaction_date"],
                    transaction_time=record["transaction_time"],
                    transaction_amount=record["transaction_amount"],
                    dr_cr_flag=record["dr_cr_flag"],

                    defaults={
                        "batch": batch,
                        **record,
                    }
                )

                total_records += 1

            except Exception as exc:
                total_errors += 1
                print(errors)
                errors.append(str(exc))

        batch.total_records = total_records
        batch.total_errors = total_errors

        if total_errors:
            batch.upload_status = "FAILED"
            batch.remarks = "\n".join(errors[:50])
        else:
            batch.upload_status = "SUCCESS"
            batch.remarks = "CBS IMPS Acquirer, Issuer and On-Us files uploaded successfully."

        batch.save()

        if total_errors:
            raise ValueError(
                f"Upload failed with {total_errors} errors. "
                f"First error: {errors[0]}"
            )

    return {
        "batch_date": batch_date,
        "acquirer_filename": acquirer_file.name,
        "issuer_filename": issuer_file.name,
        "onus_filename": onus_file.name,
        "total_records": total_records,
        "total_errors": total_errors,
        "status": "SUCCESS",
    }