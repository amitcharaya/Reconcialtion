"""
View/controller logic for the cbs application. Views receive HTTP requests, call service-layer code, and render templates or redirects.


"""
import os
import django

from gl_recon.forms import GLOpeningBalanceForm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Recon.settings')
django.setup()

from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .forms import CBSUploadForm,CBSIMPSUploadForm
from .parser import parse_cbs_record
from .models import CBSATMTransaction,UploadBatch
from django.db import transaction
from .validator import validate_cbs_record
from reconciliation.utils import normalize_date
from django.shortcuts import redirect

from cbs.services.imps_importer import import_cbs_imps_files
from datetime import date
from django.contrib import messages

from .forms import RGCSCBSUploadForm
from .models import RGCSUploadBatch, RGCSCBSTransaction
from .services.rgcs.parser import parse_rgcs_cbs_record
from .services.rgcs.validator import validate_rgcs_cbs_record
from gl_recon.services.gl_control_service import validate_gl_mapping
from .services.cbs_aggregators import cbs_summary
from gl_recon.services.gl_control_service import update_gl_balances
"""
 
"""
def process_uploaded_file(uploaded_file, expected_file_type, file_label):
    """ Helper Function to convert the flat files record and validation errors to python list of  dictionary returns  parsed_records and errors lists of dictionary"
        Arguments:
            uploaded_file {string} -- uploaded file CBs ATM File
            expected_file_type {string} -- expected file type "I", "O", "A"
            file_label {string} -- file label "Acquirer,Issuer,Onus"

        Returns:
            parsed_records {list} -- list of parsed records
            errors {list} -- list of validation errors

        read the file  line by line, validate and validation pass adds record to list
        and if failed add errors to list and return record and error list back to caller

        Usage:-  called by the function for uploading ATM CBS files
        Expected file_type= "A","I","O"
        file label "Acquirer", "Issuer", "On-Us

        Use Helper function parse_cbs_record(decoded_line) from parser.py and
         validate_cbs_record from validater.py to convert the flat file to python dictionary
         and validation errors found in transaction record


        """

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
    """ Function to upload ATM CBS files

    Display form to upload ATM CBS files
    if any CBS ATM file contains error the function aborts display error messages
    if no error found in validations records are saved and display the status message
     Use helper function process_uploaded_file to convert the lines in flat files to list python dictionary
    """

    selected_date = request.GET.get("transaction_date") or request.GET.get("batch_date")
    form = CBSUploadForm(initial={"transaction_date": selected_date} if selected_date else None)
    summary = None

    if request.method == "POST":
        form = CBSUploadForm(request.POST, request.FILES)

        if form.is_valid():

            # ✅ STEP 1: Validate GL BEFORE upload
            validation = validate_gl_mapping(
                product="ATM",
                txn_type="WITHDRAWAL",
                date=selected_date,
                request=request
            )

            if not validation["status"]:
                return redirect(validation["redirect"])
            gl=validation['gl']
            selected_date = normalize_date(form.cleaned_data["transaction_date"])
            # check if files for the date are already uploaded
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
                            print(record)
                            CBSATMTransaction.objects.create(batch=batch, **record)
                        acquirer = cbs_summary(selected_date, "A")
                        issuer = cbs_summary(selected_date, "I")
                        update_gl_balances(selected_date, acquirer, issuer, gl)
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
            print(form.errors)
            print(form.non_field_errors())

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


def process_uploaded_rgcs_file(uploaded_file, expected_file_type, file_label):
    """ Helper Function to convert the flat files record and validation errors to python list of  dictionary returns  parsed_records and errors lists of dictionary"
        Arguments:
            uploaded_file {string} -- uploaded file CBs ATM File
            expected_file_type {string} -- expected file type "I", "O", "A"
            file_label {string} -- file label "Acquirer,Issuer,Onus"

        Returns:
            parsed_records {list} -- list of parsed records
            errors {list} -- list of validation errors

        read the file  line by line, validate and validation pass adds record to list
        and if failed add errors to list and return record and error list back to caller

        Usage:-  called by the function for uploading ATM CBS files
        Expected file_type= "A","I","O"
        file label "Acquirer", "Issuer", "On-Us

        Use Helper function parse_cbs_record(decoded_line) from parser.py and
         validate_cbs_record from validater.py to convert the flat file to python dictionary
         and validation errors found in transaction record


        """

    parsed_records = []
    errors = []

    for line_number, line in enumerate(uploaded_file, start=1):
        try:
            decoded_line = line.decode("utf-8").rstrip("\n").rstrip("\r")

            if not decoded_line.strip():
                continue

            parsed_data = parse_rgcs_cbs_record(decoded_line)

            validation_errors = validate_rgcs_cbs_record(
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


def upload_rgcs_cbs_file(request):
    """ Function to upload RGCS CBS files

        Display form to upload RGCS CBS files
        if any CBS RGCS file contains error the function aborts display error messages
        if no error found in validations records are saved and display the status message

         Helper Functions used:

         Use helper parse_rgcs_cbs_record from service/rgcs/parser.py to covert flat file record to python dictionary
         validate_rgcs_cbs_record(parsed_data) from service/rgcs/validator.py to perform validations

         templates/cbs/upload_rgcs_cbs.html

        """

    result = None


    errors = []
    summary=""
    if request.method == "POST":
        form = RGCSCBSUploadForm(request.POST, request.FILES)
        selected_date = request.GET.get("transaction_date") or request.GET.get("batch_date")
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

        if RGCSUploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists():
            messages.error(request, f"Duplicate upload blocked. File already uploaded: {filename}")
            return render(request, "cbs/upload_rgcs_cbs.html", {
                "form": form,
                "result": result,
                "errors": errors,
            })
        else:
            issuer_records, issuer_errors = process_uploaded_rgcs_file(
                uploaded_file, "I", "Issuer"
            )

        for record in issuer_records:
            if normalize_date(record["transaction_date"]) != normalize_date(selected_date):
                print(normalize_date(record["transaction_date"]))
                issuer_errors.append({
                    "file": "Date Validation",
                    "line": "-",
                    "errors": [
                        f"Record date {record['transaction_date']} does not match selected upload date {selected_date}."
                    ],
                })

        if not issuer_records:
            summary = {
                "status": "failed",
                "message": "No valid CBS records found in uploaded RGCS files.",
                "errors": issuer_errors,
            }
        elif issuer_errors:
            RGCSUploadBatch.objects.create(
                batch_date=selected_date,
                source_filename=filename,

                total_records=0,
                total_errors=len(issuer_errors),
                upload_status="FAILED",
                remarks="Validation failed. No records saved.",
            )
            summary = {
                "status": "failed",
                "message": "Validation failed. No data has been saved.",
                "errors": issuer_errors,
            }
        else:
            with transaction.atomic():
                batch = RGCSUploadBatch.objects.create(
                    batch_date=selected_date,
                    source_filename=filename,
                    total_records=len(issuer_records),
                    total_errors=0,
                    upload_status="SUCCESS",
                    remarks="CBS ATM files uploaded successfully.",
                )

                for record in issuer_records:
                    record["source_filename"] = filename
                    RGCSCBSTransaction.objects.create(batch=batch, **record)

            summary = {
                "status": "success",
                "message": "All CBS files uploaded and saved successfully.",

                "issuer_count": len(issuer_records),


            }

    else:
        form = RGCSCBSUploadForm(initial={"transaction_date": request.GET.get("transaction_date") or request.GET.get("batch_date")} if (request.GET.get("transaction_date") or request.GET.get("batch_date")) else None)

    return render(request, "cbs/upload_rgcs_cbs.html", {
        "form": form,
        "summary": summary,
        "errors": errors[:100],
    })