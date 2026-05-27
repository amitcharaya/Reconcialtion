"""
Service-layer business logic for the ndpg application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import transaction

from ndpg.models import (
    NDPGIMPSRawUploadBatch,
    NDPGIMPSRawTransaction,
)

from ndpg.services.imps_raw_parser import read_ndpg_imps_raw_file


def import_ndpg_imps_raw_file(raw_file, file_type):
    parsed_data = read_ndpg_imps_raw_file(raw_file, file_type)

    header = parsed_data["header"]
    records = parsed_data["records"]
    eof_record_count = parsed_data["eof_record_count"]

    file_date = header["file_date"]
    cycle_no = header["cycle_no"]
    raw_header = header["raw_header"]
    source_filename = raw_file.name

    duplicate_exists = NDPGIMPSRawUploadBatch.objects.filter(
        file_type=file_type,
        file_date=file_date,
        cycle_no=cycle_no,
        source_filename=source_filename,
        upload_status="SUCCESS",
    ).exists()

    if duplicate_exists:
        raise ValueError(
            f"Duplicate upload blocked. File already uploaded successfully: "
            f"{source_filename}, {file_type}, {file_date}, Cycle {cycle_no}."
        )

    with transaction.atomic():

        batch = NDPGIMPSRawUploadBatch.objects.create(
            file_type=file_type,
            file_date=file_date,
            cycle_no=cycle_no,
            raw_header=raw_header,
            source_filename=source_filename,
            eof_record_count=eof_record_count,
            total_records=len(records),
            upload_status="FAILED",
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        try:
            for record in records:

                obj, created = NDPGIMPSRawTransaction.objects.update_or_create(
                    transaction_serial_number=record["transaction_serial_number"],
                    actual_transaction_amount=record["actual_transaction_amount"],
                    file_type=file_type,
                    cycle_no=cycle_no,
                    file_date=file_date,
                    defaults={
                        "batch": batch,
                        "participant_id": record.get("participant_id"),
                        "transaction_type": record.get("transaction_type"),
                        "from_account_type": record.get("from_account_type"),
                        "to_account_type": record.get("to_account_type"),
                        "response_code": record.get("response_code"),
                        "pan_number": record.get("pan_number"),
                        "approval_no": record.get("approval_no"),
                        "transaction_date": record.get("transaction_date"),
                        "transaction_time": record.get("transaction_time"),
                        "merchant_category_code": record.get(
                            "merchant_category_code"
                        ),
                        "card_acceptor_settlement_date": record.get(
                            "card_acceptor_settlement_date"
                        ),
                        "card_acceptor_id": record.get("card_acceptor_id"),
                        "acquirer_id": record.get("acquirer_id"),
                        "transaction_currency_code": record.get(
                            "transaction_currency_code"
                        ),
                        "original_channel": record.get("original_channel"),
                        "bene_ifsc_code": record.get("bene_ifsc_code"),
                        "bene_account_no": record.get("bene_account_no"),
                        "rem_ifsc_code": record.get("rem_ifsc_code"),
                        "remitter_account_no": record.get(
                            "remitter_account_no"
                        ),
                        "source_filename": source_filename,
                        "raw_header": raw_header,
                        "eof_record_count": eof_record_count,
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            batch.created_records = created_count
            batch.updated_records = updated_count
            batch.skipped_records = skipped_count
            batch.upload_status = "SUCCESS"
            batch.save()

        except Exception as exc:
            batch.error_message = str(exc)
            batch.upload_status = "FAILED"
            batch.save()
            raise

    return {
        "filename": source_filename,
        "file_type": file_type,
        "file_date": file_date,
        "cycle_no": cycle_no,
        "raw_header": raw_header,
        "total_records": len(records),
        "eof_record_count": eof_record_count,
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "upload_status": "SUCCESS",
    }