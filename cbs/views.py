"""
View/controller logic for the cbs application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .forms import CBSUploadForm,CBSIMPSUploadForm
from .parser import parse_cbs_record
from .models import CBSATMTransaction,UploadBatch
from django.db import transaction
from .validator import validate_cbs_record
from reconciliation.utils import normalize_date


from cbs.services.imps_importer import import_cbs_imps_files
from datetime import date
from django.contrib import messages

from .forms import RGCSCBSUploadForm
from .models import RGCSUploadBatch, RGCSCBSTransaction
from .services.rgcs.parser import parse_rgcs_cbs_record
from .services.rgcs.validator import validate_rgcs_cbs_record



def process_uploaded_file(uploaded_file, expected_file_type, file_label):
    parsed_records = []
    errors = []

    for line_number, line in enumerate(uploaded_file, start=1):
        try:
            decoded_line = line.decode("utf-8").rstrip("\n").rstrip("\r")

            if not decoded_line.strip():
                continue

            parsed_data = parse_cbs_record(decoded_line)

            validation_errors = validate_cbs_record(
                parsed_data,
                decoded_line,
                expected_file_type
            )

            if validation_errors:
                errors.append({
                    "file": file_label,
                    "line": line_number,
                    "errors": validation_errors,
                })
            else:
                parsed_records.append(parsed_data)

        except Exception as e:
            errors.append({
                "file": file_label,
                "line": line_number,
                "errors": [str(e)],
            })

    return parsed_records, errors


def upload_cbs_files(request):
    selected_date = request.GET.get("transaction_date") or request.GET.get("batch_date")
    form = CBSUploadForm(initial={"transaction_date": selected_date} if selected_date else None)
    summary = None

    if request.method == "POST":
        form = CBSUploadForm(request.POST, request.FILES)

        if form.is_valid():
            selected_date = normalize_date(form.cleaned_data["transaction_date"])

            if UploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists():
                summary = {
                    "status": "failed",
                    "message": f"CBS files for date {selected_date} have already been uploaded.",
                }
            else:
                acquirer_records, acquirer_errors = process_uploaded_file(
                    request.FILES["acquirer_file"], "A", "Acquirer"
                )
                issuer_records, issuer_errors = process_uploaded_file(
                    request.FILES["issuer_file"], "I", "Issuer"
                )
                onus_records, onus_errors = process_uploaded_file(
                    request.FILES["onus_file"], "O", "On-Us"
                )

                all_errors = acquirer_errors + issuer_errors + onus_errors
                all_records = acquirer_records + issuer_records + onus_records

                for record in all_records:
                    if normalize_date(record["txn_date"]) != selected_date:
                        all_errors.append({
                            "file": "Date Validation",
                            "line": "-",
                            "errors": [
                                f"Record date {record['txn_date']} does not match selected upload date {selected_date}."
                            ],
                        })

                if not all_records:
                    summary = {
                        "status": "failed",
                        "message": "No valid CBS records found in uploaded files.",
                        "errors": all_errors,
                    }
                elif all_errors:
                    UploadBatch.objects.create(
                        batch_date=selected_date,
                        acquirer_filename=request.FILES["acquirer_file"].name,
                        issuer_filename=request.FILES["issuer_file"].name,
                        onus_filename=request.FILES["onus_file"].name,
                        total_records=0,
                        total_errors=len(all_errors),
                        upload_status="FAILED",
                        remarks="Validation failed. No records saved.",
                    )
                    summary = {
                        "status": "failed",
                        "message": "Validation failed. No data has been saved.",
                        "errors": all_errors,
                    }
                else:
                    with transaction.atomic():
                        batch = UploadBatch.objects.create(
                            batch_date=selected_date,
                            acquirer_filename=request.FILES["acquirer_file"].name,
                            issuer_filename=request.FILES["issuer_file"].name,
                            onus_filename=request.FILES["onus_file"].name,
                            total_records=len(all_records),
                            total_errors=0,
                            upload_status="SUCCESS",
                            remarks="CBS ATM files uploaded successfully.",
                        )
                        for record in all_records:
                            CBSATMTransaction.objects.create(batch=batch, **record)

                    summary = {
                        "status": "success",
                        "message": "All CBS files uploaded and saved successfully.",
                        "acquirer_count": len(acquirer_records),
                        "issuer_count": len(issuer_records),
                        "onus_count": len(onus_records),
                        "total_count": len(all_records),
                    }

    return render(request, "cbs/upload.html", {"form": form, "summary": summary})



"imps upload"


def upload_cbs_imps_files(request):
    summary = None
    error = None

    if request.method == "POST":
        form = CBSIMPSUploadForm(request.POST, request.FILES)

        if form.is_valid():
            acquirer_file = request.FILES["acquirer_file"]
            issuer_file = request.FILES["issuer_file"]
            onus_file = request.FILES["onus_file"]

            try:
                summary = import_cbs_imps_files(
                    acquirer_file=acquirer_file,
                    issuer_file=issuer_file,
                    onus_file=onus_file,
                )

            except Exception as exc:
                error = str(exc)

    else:
        form = CBSIMPSUploadForm(initial={"transaction_date": request.GET.get("transaction_date")} if request.GET.get("transaction_date") else None)

    return render(
        request,
        "cbs/upload_imps.html",
        {
            "form": form,
            "summary": summary,
            "error": error,
        }
    )



"RGCS Upload"



def upload_rgcs_cbs_file(request):
    result = None
    errors = []

    if request.method == "POST":
        form = RGCSCBSUploadForm(request.POST, request.FILES)

        if not request.FILES:
            messages.error(request, "No file received by server. Check form enctype and input name.")

        if not form.is_valid():
            messages.error(request, "Form is not valid. Please check the errors below.")
            return render(request, "cbs/upload_rgcs_cbs.html", {
                "form": form,
                "result": result,
                "errors": errors,
            })

        uploaded_file = form.cleaned_data["rgcs_file"]
        filename = uploaded_file.name

        if not filename.lower().endswith(".rc"):
            messages.error(request, "Invalid file extension. Only .RC file is allowed.")
            return render(request, "cbs/upload_rgcs_cbs.html", {
                "form": form,
                "result": result,
                "errors": errors,
            })

        if RGCSUploadBatch.objects.filter(source_filename=filename).exists():
            messages.error(request, f"Duplicate upload blocked. File already uploaded: {filename}")
            return render(request, "cbs/upload_rgcs_cbs.html", {
                "form": form,
                "result": result,
                "errors": errors,
            })

        total_records = 0
        total_errors = 0

        try:
            batch_date = form.cleaned_data["transaction_date"]
            with transaction.atomic():
                batch = RGCSUploadBatch.objects.create(
                    batch_date=batch_date,
                    source_filename=filename,
                    upload_status="SUCCESS",
                    remarks=f"RGCS CBS upload started: {filename}",
                )

                for line_no, raw_line in enumerate(uploaded_file, start=1):
                    try:
                        line = raw_line.decode("utf-8", errors="ignore").rstrip("\r\n")

                        parsed_data = parse_rgcs_cbs_record(line)

                        if parsed_data is None:
                            continue

                        validation_errors = validate_rgcs_cbs_record(parsed_data)

                        if validation_errors:
                            total_errors += 1
                            errors.append({
                                "line_no": line_no,
                                "error": "; ".join(validation_errors),
                            })
                            continue

                        RGCSCBSTransaction.objects.create(
                            batch=batch,
                            source_filename=filename,
                            **parsed_data
                        )

                        total_records += 1

                    except Exception as e:
                        total_errors += 1
                        errors.append({
                            "line_no": line_no,
                            "error": str(e),
                        })

                if total_records == 0:
                    batch.upload_status = "FAILED"
                elif total_errors > 0:
                    batch.upload_status = "PARTIAL"
                else:
                    batch.upload_status = "SUCCESS"

                batch.total_records = total_records
                batch.total_errors = total_errors
                batch.remarks = f"RGCS CBS upload completed: {filename}"
                batch.save()

            result = {
                "filename": filename,
                "total_records": total_records,
                "total_errors": total_errors,
                "status": batch.upload_status,
            }

            messages.success(
                request,
                f"Upload processed. Records saved: {total_records}, Errors: {total_errors}"
            )

        except Exception as e:
            messages.error(request, f"Upload failed: {str(e)}")

    else:
        form = RGCSCBSUploadForm(initial={"transaction_date": request.GET.get("transaction_date") or request.GET.get("batch_date")} if (request.GET.get("transaction_date") or request.GET.get("batch_date")) else None)

    return render(request, "cbs/upload_rgcs_cbs.html", {
        "form": form,
        "result": result,
        "errors": errors[:100],
    })