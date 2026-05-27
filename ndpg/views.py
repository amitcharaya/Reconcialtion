"""
View/controller logic for the ndpg application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.shortcuts import render

from ndpg.forms import NDPGIMPSRawUploadForm
from ndpg.services.imps_raw_importer import import_ndpg_imps_raw_file

from reconciliation.utils import normalize_date
from .parser import (
    parse_ndpg_acquirer_record,
    parse_ndpg_issuer_record,
)

from .validator import validate_ndpg_record
from django.db import transaction
from django.shortcuts import render

from .forms import NDPGUploadForm
from .models import NDPGATMTransaction,NDPGUploadBatch
from reconciliation.utils import normalize_date
from reconciliation.services.next_day_ndpg_matcher import auto_match_next_day_ndpg
from ndpg.models import NDPGIMPSRawTransaction
from ndpg.services.imps_raw_parser import read_ndpg_imps_raw_file

from .forms import RGCSRawUploadForm
from .models import RGCSUploadBatch, RGCSRawTransaction
from .services.rgcs_raw_parser import parse_rgcs_file
from .services.rgcs_raw_validator import (
    validate_rgcs_record,
    validate_trailer,
    check_duplicate_file,
)


def process_ndpg_file(uploaded_file, file_type, cycle_no):

    parsed_records = []
    errors = []

    for line_number, line in enumerate(uploaded_file, start=1):

        try:
            decoded_line = line.decode("utf-8").rstrip("\n").rstrip("\r")

            if not decoded_line.strip():
                continue

            if file_type == "ACQUIRER":
                parsed_data = parse_ndpg_acquirer_record(
                    decoded_line,
                    cycle_no
                )

            else:
                parsed_data = parse_ndpg_issuer_record(
                    decoded_line,
                    cycle_no
                )

            validation_errors = validate_ndpg_record(
                parsed_data,
                decoded_line,
                file_type
            )

            if validation_errors:
                errors.append({
                    "cycle": cycle_no,
                    "file_type": file_type,
                    "line": line_number,
                    "errors": validation_errors,
                })

            else:
                parsed_records.append(parsed_data)

        except Exception as e:
            errors.append({
                "cycle": cycle_no,
                "file_type": file_type,
                "line": line_number,
                "errors": [str(e)],
            })

    return parsed_records, errors


# Create your views here.
def upload_ndpg_files(request):

    form = NDPGUploadForm(initial={"upload_date": request.GET.get("transaction_date") or request.GET.get("upload_date")} if (request.GET.get("transaction_date") or request.GET.get("upload_date")) else None)
    summary = None

    if request.method == "POST":

        form = NDPGUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            all_records = []
            all_errors = []

            for cycle_no in ["1", "2", "3", "4"]:

                acquirer_file = request.FILES[
                    f"cycle_{cycle_no}_acquirer"
                ]

                issuer_file = request.FILES[
                    f"cycle_{cycle_no}_issuer"
                ]

                acq_records, acq_errors = process_ndpg_file(
                    acquirer_file,
                    "ACQUIRER",
                    cycle_no
                )

                iss_records, iss_errors = process_ndpg_file(
                    issuer_file,
                    "ISSUER",
                    cycle_no
                )

                all_records.extend(acq_records)
                all_records.extend(iss_records)

                all_errors.extend(acq_errors)
                all_errors.extend(iss_errors)

            if all_errors:

                summary = {
                    "status": "failed",
                    "message": "Validation failed. No NDPG data saved.",
                    "errors": all_errors,
                }

            else:
                upload_date = normalize_date(form.cleaned_data["upload_date"])

                if NDPGUploadBatch.objects.filter(upload_date=upload_date).exists():
                    summary = {
                        "status": "failed",
                        "message": f"NDPG files for date {upload_date} have already been uploaded.",
                    }
                with transaction.atomic():
                    batch = NDPGUploadBatch.objects.create(
                        upload_date=normalize_date(upload_date),
                        total_records=len(all_records),

                        cycle_1_acquirer_filename=request.FILES["cycle_1_acquirer"].name,
                        cycle_1_issuer_filename=request.FILES["cycle_1_issuer"].name,
                        cycle_2_acquirer_filename=request.FILES["cycle_2_acquirer"].name,
                        cycle_2_issuer_filename=request.FILES["cycle_2_issuer"].name,
                        cycle_3_acquirer_filename=request.FILES["cycle_3_acquirer"].name,
                        cycle_3_issuer_filename=request.FILES["cycle_3_issuer"].name,
                        cycle_4_acquirer_filename=request.FILES["cycle_4_acquirer"].name,
                        cycle_4_issuer_filename=request.FILES["cycle_4_issuer"].name,
                    )
                    for record in all_records:
                        NDPGATMTransaction.objects.create(batch=batch,
                            **record
                        )
                    auto_match_next_day_ndpg(upload_date)

                summary = {
                    "status": "success",
                    "message": "All NDPG cycles uploaded successfully.",
                    "total_records": len(all_records),
                }

    return render(
        request,
        "ndpg/upload.html",
        {
            "form": form,
            "summary": summary,
        }
    )

"IMPS Section"



def upload_ndpg_imps_raw_view(request):
    summaries = []
    error = None

    if request.method == "POST":
        form = NDPGIMPSRawUploadForm(request.POST, request.FILES)

        if form.is_valid():
            upload_date = form.cleaned_data["upload_date"]
            file_type = form.cleaned_data["file_type"]
            raw_files = request.FILES.getlist("raw_files")

            try:
                for raw_file in raw_files:
                    summary = import_ndpg_imps_raw_file(
                        raw_file=raw_file,
                        file_type=file_type,
                    )

                    summaries.append(summary)

            except Exception as exc:
                error = str(exc)

    else:
        form = NDPGIMPSRawUploadForm(initial={"upload_date": request.GET.get("transaction_date") or request.GET.get("upload_date")} if (request.GET.get("transaction_date") or request.GET.get("upload_date")) else None)

    return render(
        request,
        "ndpg/upload_imps_raw.html",
        {
            "form": form,
            "summaries": summaries,
            "error": error,
        }
    )

"""RGCS Section"

"""


def upload_rgcs_raw_files(request):
    context = {}

    if request.method == "POST":
        form = RGCSRawUploadForm(request.POST, request.FILES)

        if form.is_valid():
            batch_date = form.cleaned_data["batch_date"]
            record_nature = form.cleaned_data["record_nature"]

            uploaded_files = {
                "file_861": form.cleaned_data.get("file_861"),
                "file_862": form.cleaned_data.get("file_862"),
                "file_863": form.cleaned_data.get("file_863"),
                "file_864": form.cleaned_data.get("file_864"),
            }

            errors = []
            parsed_files = {}
            total_records = 0

            for file_key, uploaded_file in uploaded_files.items():
                if not uploaded_file:
                    continue

                source_filename = uploaded_file.name

                if check_duplicate_file(source_filename):
                    errors.append(f"Duplicate upload blocked: {source_filename}")
                    continue

                try:
                    parsed_file = parse_rgcs_file(uploaded_file)
                    parsed_files[file_key] = {
                        "filename": source_filename,
                        "parsed_file": parsed_file,
                    }

                    errors.extend(validate_trailer(parsed_file, source_filename))

                    for index, record in enumerate(parsed_file["records"], start=1):
                        errors.extend(
                            validate_rgcs_record(
                                record,
                                index,
                                source_filename
                            )
                        )

                    total_records += len(parsed_file["records"])

                except Exception as exc:
                    errors.append(f"{source_filename}: {str(exc)}")

            if errors:
                context["form"] = form
                context["status"] = "FAILED"
                context["message"] = "Upload failed."
                context["errors"] = errors[:50]
                return render(request, "ndpg/upload_rgcs_raw.html", context)

            try:
                with transaction.atomic():
                    batch = RGCSUploadBatch.objects.create(
                        batch_date=batch_date,
                        record_nature=record_nature,
                        file_861=parsed_files.get("file_861", {}).get("filename"),
                        file_862=parsed_files.get("file_862", {}).get("filename"),
                        file_863=parsed_files.get("file_863", {}).get("filename"),
                        file_864=parsed_files.get("file_864", {}).get("filename"),
                        total_records=total_records,
                        total_errors=0,
                        upload_status="SUCCESS",
                        remarks="RGCS raw files uploaded successfully.",
                    )

                    transactions = []

                    for file_key, file_info in parsed_files.items():
                        source_filename = file_info["filename"]
                        parsed_file = file_info["parsed_file"]

                        for record in parsed_file["records"]:
                            transactions.append(
                                RGCSRawTransaction(
                                    batch=batch,
                                    record_nature=record_nature,
                                    source_filename=source_filename,
                                    **record
                                )
                            )

                    RGCSRawTransaction.objects.bulk_create(transactions)

                context["status"] = "SUCCESS"
                context["message"] = f"Upload successful. {total_records} records imported."

            except Exception as exc:
                context["status"] = "FAILED"
                context["message"] = f"Upload failed: {str(exc)}"

        else:
            context["status"] = "FAILED"
            context["message"] = "Form is not valid. Please check the errors below."

    else:
        form = RGCSRawUploadForm(initial={"batch_date": request.GET.get("transaction_date") or request.GET.get("batch_date")} if (request.GET.get("transaction_date") or request.GET.get("batch_date")) else None)

    context["form"] = form
    return render(request, "ndpg/upload_rgcs_raw.html", context)