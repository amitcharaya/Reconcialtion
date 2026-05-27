"""
View/controller logic for the switchlog application. Views receive HTTP requests, call service-layer code, and render templates or redirects.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

import pandas as pd
from decimal import Decimal
from reconciliation.utils import normalize_date
from django.shortcuts import render
from django.db import transaction

from .forms import SwitchLogUploadForm,SwitchIMPSUploadForm
from .models import SwitchATMTransaction,SwitchLogUploadBatch
from reconciliation.utils import normalize_datetime, normalize_date
import pandas as pd
from decimal import Decimal
import math
import pandas as pd
from django.shortcuts import render
from django.db import transaction
from django.contrib import messages

from .forms import SwitchIMPSUploadForm
from .models import SwitchIMPSUploadBatch, SwitchIMPSTransaction
from .utils import (
    COLUMN_MAP,
    REQUIRED_FIELDS,
    clean_value,
    parse_decimal,
    parse_datetime,
    get_transaction_amount,
)




def clean_json_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, Decimal):
        return str(value)

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def clean_row_for_json(row):
    return {
        str(key): clean_json_value(value)
        for key, value in row.to_dict().items()
    }
def clean_amount(value):
    if value is None or value == "":
        return Decimal("0.00")

    return Decimal(str(value)).quantize(Decimal("0.01"))

def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()
def upload_switch_log(request):
    form = SwitchLogUploadForm(initial={"upload_date": request.GET.get("transaction_date") or request.GET.get("upload_date")} if (request.GET.get("transaction_date") or request.GET.get("upload_date")) else None)
    summary = None

    if request.method == "POST":
        form = SwitchLogUploadForm(request.POST, request.FILES)

        if form.is_valid():
            switch_file = request.FILES["switch_file"]

            try:
                df = pd.read_excel(switch_file)
                if df.empty:
                    summary = {
                        "status": "failed",
                        "message": "Switch log file is empty.",
                    }
                else:
                    upload_date = normalize_date(form.cleaned_data["upload_date"])

                    if SwitchLogUploadBatch.objects.filter(upload_date=upload_date).exists():
                        summary = {
                            "status": "failed",
                            "message": f"Switch log for date {upload_date} has already been uploaded.",
                        }
                    else:
                        records_to_save = []
                        errors = []


                        for index, row in df.iterrows():

                            try:
                                record = SwitchATMTransaction(
                                    sn=str(row.get("SN", "")).strip(),
                                    transaction_datetime=normalize_datetime(row.get("TRANX DATE")),
                                    transaction_date=normalize_date(row.get("TRANX DATE")),

                                    terminal_id=str(row.get("TERMINAL ID", "")).strip(),
                                    terminal_type=str(row.get("TERMINAL TYPE", "")).strip(),
                                    switch=str(row.get("SWITCH", "")).strip(),

                                    stan_no=str(row.get("STAN NO", "")).strip(),
                                    card_no=str(row.get("CARD NO.", "")).strip(),

                                    account_type=str(row.get("ACCOUNT TYPE", "")).strip(),
                                    account_no=str(row.get("ACCOUNT NO.", "")).strip(),
                                    beneficiary_account_no=str(row.get("BENEFICIARY A/C NO.", "")).strip(),

                                    acquirer_bank=str(row.get("ACQ.BANK", "")).strip(),
                                    rrn=str(row.get("RET REF NO.", "")).strip(),
                                    mcc=str(row.get("MCC", "")).strip(),

                                    transaction_type=str(row.get("TXN.TYPE", "")).strip(),
                                    connected_transaction=str(row.get("CON.TXN.", "")).strip(),
                                    transaction_description=str(row.get("TXN. DESC.", "")).strip(),

                                    amount_requested=clean_amount(row.get("AMOUNT REQ.", 0)),
                                    transaction_amount=clean_amount(row.get("AMOUNT APPROVED", 0)),

                                    interface_type=str(row.get("INTF. TYPE", "")).strip(),
                                    void_code=str(row.get("VOID CODE", "")).strip(),
                                    atm_location=str(row.get("ATM LOCATION", "")).strip(),
                                    embossed_name=str(row.get("EMBOSSED NAME", "")).strip(),

                                    transaction_status=str(row.get("STATUS", "")).strip(),
                                    error=str(row.get("ERROR", "")).strip(),

                                    raw_data=clean_row_for_json(row)
                                )

                                records_to_save.append(record)

                            except Exception as e:
                                errors.append({
                                    "row": index + 2,
                                    "error": str(e)
                                })

                        if errors:
                            summary = {
                                "status": "failed",
                                "message": "Validation failed. No switch log data saved.",
                                "errors": errors,
                            }

                        else:
                            with transaction.atomic():
                                batch = SwitchLogUploadBatch.objects.create(
                                    upload_date=upload_date,
                                    filename=switch_file.name,
                                    total_records=len(records_to_save),
                                )
                                for record in records_to_save:
                                    record.batch = batch

                                SwitchATMTransaction.objects.bulk_create(records_to_save)

                            summary = {
                                "status": "success",
                                "message": "Switch log uploaded successfully.",
                                "total_records": len(records_to_save),
                            }

            except Exception as e:
                summary = {
                    "status": "failed",
                    "message": str(e),
                }

    return render(
        request,
        "switchlog/upload.html",
        {
            "form": form,
            "summary": summary,
        }
    )

"IMPS code"




def upload_switch_imps_file(request):
    context = {}

    if request.method == "POST":
        form = SwitchIMPSUploadForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES.get("switch_imps_file")

            if not uploaded_file:
                raise ValueError("No Switch IMPS file selected for upload.")

            try:
                df = pd.read_excel(uploaded_file)

                df.columns = [str(col).strip() for col in df.columns]

                mapped_columns = {}

                for col in df.columns:
                    if col in COLUMN_MAP:
                        mapped_columns[col] = COLUMN_MAP[col]

                df = df.rename(columns=mapped_columns)

                missing_fields = [
                    field for field in REQUIRED_FIELDS
                    if field not in df.columns
                ]

                if missing_fields:
                    raise ValueError(
                        f"Missing required columns in Switch IMPS file: {missing_fields}. "
                        f"Columns mapped: {mapped_columns}. "
                        f"Actual columns: {list(df.columns)}"
                    )

                first_valid_date = None

                for _, row in df.iterrows():
                    if pd.notna(row.get("transaction_datetime")):
                        first_valid_date = parse_datetime(row.get("transaction_datetime")).date()
                        break

                if not first_valid_date:
                    raise ValueError("Could not determine batch date from Switch IMPS file.")

                if SwitchIMPSUploadBatch.objects.filter(
                    batch_date=first_valid_date,
                    filename=uploaded_file.name
                ).exists():
                    raise ValueError(
                        f"This Switch IMPS file is already uploaded for date {first_valid_date}."
                    )

                errors = []
                success_count = 0

                with transaction.atomic():
                    batch = SwitchIMPSUploadBatch.objects.create(
                        batch_date=first_valid_date,
                        filename=uploaded_file.name,
                        upload_status="SUCCESS",
                    )

                    for index, row in df.iterrows():
                        try:
                            transaction_datetime = parse_datetime(row.get("transaction_datetime"))

                            debit_amount = parse_decimal(row.get("debit_amount"))
                            credit_amount = parse_decimal(row.get("credit_amount"))
                            transaction_amount = get_transaction_amount(
                                row.get("debit_amount"),
                                row.get("credit_amount")
                            )

                            transaction_id = clean_value(row.get("transaction_id"))
                            rrn = clean_value(row.get("rrn"))

                            if not transaction_id:
                                raise ValueError("Transaction Id is missing")

                            if not rrn:
                                raise ValueError("RRN No. is missing")

                            SwitchIMPSTransaction.objects.create(
                                batch=batch,
                                transaction_datetime=transaction_datetime,
                                transaction_id=transaction_id,
                                transaction_category=clean_value(row.get("transaction_category")),
                                transaction_type=clean_value(row.get("transaction_type")),
                                transaction_particulars=clean_value(row.get("transaction_particulars")),

                                debit_amount=debit_amount,
                                credit_amount=credit_amount,
                                transaction_amount=transaction_amount,

                                status=clean_value(row.get("status")),
                                rrn=rrn,

                                rem_mmid=clean_value(row.get("rem_mmid")),
                                rem_account=clean_value(row.get("rem_account")),
                                remitter_name=clean_value(row.get("remitter_name")),
                                rem_mobile=clean_value(row.get("rem_mobile")),

                                bene_mas=clean_value(row.get("bene_mas")),
                                bene_nbin=clean_value(row.get("bene_nbin")),
                                bene_mobile=clean_value(row.get("bene_mobile")),
                                bene_account=clean_value(row.get("bene_account")),
                                beneficiary_name=clean_value(row.get("beneficiary_name")),
                                beneficiary_ifsc=clean_value(row.get("beneficiary_ifsc")),

                                product_indicator=clean_value(row.get("product_indicator")),
                                original_channel=clean_value(row.get("original_channel")),

                                cbs_status=clean_value(row.get("cbs_status")),
                                cbs_rc=clean_value(row.get("cbs_rc")),
                                cbs_reversal_status=clean_value(row.get("cbs_reversal_status")),
                                cbs_reversal_rc=clean_value(row.get("cbs_reversal_rc")),

                                nfs_status=clean_value(row.get("nfs_status")),
                                nfs_verification_status=clean_value(row.get("nfs_verification_status")),
                                nfs_verification_rc=clean_value(row.get("nfs_verification_rc")),

                                imps_rc=clean_value(row.get("imps_rc")),
                                remark=clean_value(row.get("remark")),
                                description=clean_value(row.get("description")),

                                raw_data=row.where(pd.notnull(row), None).to_dict(),
                            )

                            success_count += 1

                        except Exception as row_error:
                            errors.append(f"Row {index + 2}: {row_error}")

                    batch.total_records = success_count
                    batch.total_errors = len(errors)

                    if errors:
                        batch.upload_status = "FAILED"
                        batch.remarks = "\n".join(errors[:20])
                    else:
                        batch.upload_status = "SUCCESS"
                        batch.remarks = "Switch IMPS file uploaded successfully."

                    batch.save()

                if errors:
                    messages.error(
                        request,
                        f"Upload completed with {len(errors)} errors. First error: {errors[0]}"
                    )
                else:
                    messages.success(
                        request,
                        f"Switch IMPS file uploaded successfully. Total records: {success_count}"
                    )

                context["success_count"] = success_count
                context["errors"] = errors

            except Exception as e:
                messages.error(request, f"Upload Failed: {e}")
                context["error"] = str(e)

    else:
        form = SwitchIMPSUploadForm(initial={"upload_date": request.GET.get("transaction_date") or request.GET.get("upload_date")} if (request.GET.get("transaction_date") or request.GET.get("upload_date")) else None)

    context["form"] = form
    return render(request, "switchlog/upload_switch_imps.html", context)

"""
RGCS Section
"""

from django.shortcuts import render
from django.db import transaction

from .forms import RGCSSwitchUploadForm
from .models import RGCSSwitchUploadBatch, RGCSSwitchTransaction
from .services.rgcs_switch_parser import parse_rgcs_switch_excel
from .services.rgcs_switch_validator import (
    validate_rgcs_switch_columns,
    validate_rgcs_switch_record,
    check_duplicate_rgcs_switch_file,
)


def upload_rgcs_switch_file(request):
    context = {}

    if request.method == "POST":
        form = RGCSSwitchUploadForm(request.POST, request.FILES)

        if form.is_valid():
            batch_date = form.cleaned_data["batch_date"]
            uploaded_file = form.cleaned_data["switch_file"]
            source_filename = uploaded_file.name

            errors = []

            if check_duplicate_rgcs_switch_file(source_filename):
                errors.append(f"Duplicate upload blocked: {source_filename}")

            if not errors:
                try:
                    parsed_file = parse_rgcs_switch_excel(uploaded_file)

                    errors.extend(
                        validate_rgcs_switch_columns(parsed_file["columns"])
                    )

                    for index, record in enumerate(parsed_file["records"], start=2):
                        errors.extend(
                            validate_rgcs_switch_record(record, index)
                        )

                    if errors:
                        context["status"] = "FAILED"
                        context["message"] = "Upload failed due to validation errors."
                        context["errors"] = errors[:50]
                        context["form"] = form
                        return render(request, "switchlog/upload_rgcs_switch.html", context)

                    with transaction.atomic():
                        batch = RGCSSwitchUploadBatch.objects.create(
                            batch_date=batch_date,
                            source_filename=source_filename,
                            total_records=len(parsed_file["records"]),
                            total_errors=0,
                            upload_status="SUCCESS",
                            remarks="RGCS switch file uploaded successfully.",
                        )

                        transactions = []

                        for record in parsed_file["records"]:
                            transactions.append(
                                RGCSSwitchTransaction(
                                    batch=batch,
                                    source_filename=source_filename,
                                    **record
                                )
                            )

                        RGCSSwitchTransaction.objects.bulk_create(transactions)

                    context["status"] = "SUCCESS"
                    context["message"] = (
                        f"RGCS switch upload successful. "
                        f"{len(parsed_file['records'])} records imported."
                    )

                except Exception as exc:
                    context["status"] = "FAILED"
                    context["message"] = f"Upload failed: {str(exc)}"

        else:
            context["status"] = "FAILED"
            context["message"] = "Form is not valid. Please check the errors below."

    else:
        form = RGCSSwitchUploadForm(initial={"batch_date": request.GET.get("transaction_date") or request.GET.get("batch_date")} if (request.GET.get("transaction_date") or request.GET.get("batch_date")) else None)

    context["form"] = form
    return render(request, "switchlog/upload_rgcs_switch.html", context)