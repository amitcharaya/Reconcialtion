from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .forms import ATMSettlementUploadForm
from .models import ATMSettlementCycle, ATMSettlementItem
from .services.parser import validate_atm_ntsl_filename, parse_atm_ntsl_file


# atm_settlement/views.py
from gl_recon.services.gl_control_service import validate_gl_mapping


def upload_atm_settlement(request):
    if request.method == "POST":
        form = ATMSettlementUploadForm(request.POST, request.FILES)

        if form.is_valid():
            settlement_files = request.FILES.getlist("settlement_files")
            settlement_date, cycle_no = validate_atm_ntsl_filename(settlement_files[0].name)
            validation = validate_gl_mapping(
                product="ATM",
                txn_type="SETTLEMENT",
                date=settlement_date,
                request=request
            )

            # ❌ If validation fails → redirect
            if not validation["status"]:
                return redirect(validation["redirect"])

            # ✔ If success → get GL
            gl = validation["gl"]
            if len(settlement_files) != 4:
                messages.error(request, "Please upload exactly 4 ATM NTSL cycle files.")
                return redirect("upload_atm_settlement")

            uploaded_count = 0

            for settlement_file in settlement_files:
                try:

                    settlement_date, cycle_no = validate_atm_ntsl_filename(settlement_file.name)
                    if ATMSettlementCycle.objects.filter(
                        settlement_date=settlement_date,
                        cycle_no=cycle_no
                    ).exists():
                        messages.warning(request, f"{settlement_file.name} already uploaded. Skipped.")
                        continue

                    cycle = ATMSettlementCycle.objects.create(
                        settlement_date=settlement_date,
                        cycle_no=cycle_no,
                        original_filename=settlement_file.name,
                        uploaded_file=settlement_file,
                    )

                    parsed_data = parse_atm_ntsl_file(cycle.uploaded_file.path)

                    cycle.issuer_sub_total = parsed_data["issuer_sub_total"]
                    cycle.acquirer_sub_total = parsed_data["acquirer_sub_total"]
                    cycle.settlement_amount = parsed_data["settlement_amount"]
                    cycle.net_adjusted_amount = parsed_data["net_adjusted_amount"]
                    cycle.final_settlement_amount = parsed_data["final_settlement_amount"]
                    cycle.save()

                    for item in parsed_data["items"]:
                        ATMSettlementItem.objects.create(
                            settlement_cycle=cycle,
                            description=item["description"],
                            txn_count=item["txn_count"],
                            debit_amount=item["debit_amount"],
                            credit_amount=item["credit_amount"],
                        )

                    uploaded_count += 1

                except Exception as e:
                    messages.error(request, f"{settlement_file.name}: {e}")

            messages.success(request, f"{uploaded_count} ATM NTSL files uploaded successfully.")
            return redirect("atm_settlement_list")

    else:
        form = ATMSettlementUploadForm()

    return render(request, "atm_settlement/upload.html", {"form": form})


def atm_settlement_list(request):
    cycles = ATMSettlementCycle.objects.all().order_by("-settlement_date", "cycle_no")
    return render(request, "atm_settlement/list.html", {"cycles": cycles})


def atm_settlement_detail(request, cycle_id):
    cycle = get_object_or_404(ATMSettlementCycle, id=cycle_id)
    items = cycle.items.all().order_by("id")

    summary = {
        "acquirer_withdrawal_amount": items.filter(
            description__iexact="Acquirer WDL Transaction Amount"
        ).first(),

        "issuer_withdrawal_amount": items.filter(
            description__iexact="Issuer WDL Transaction Amount"
        ).first(),

        "acquirer_wdl_fee": items.filter(
            description__iexact="Acquirer WDL Approved Fee"
        ).first(),

        "acquirer_wdl_fee_gst": items.filter(
            description__iexact="Acquirer WDL Approved Fee - GST"
        ).first(),

        "issuer_wdl_fee": items.filter(
            description__iexact="Issuer WDL Approved Fee"
        ).first(),

        "issuer_wdl_fee_gst": items.filter(
            description__iexact="Issuer WDL Approved Fee - GST"
        ).first(),

        "issuer_wdl_switching_fee": items.filter(
            description__iexact="Issuer WDL Approved NPCI Switching Fee"
        ).first(),

        "issuer_wdl_switching_fee_gst": items.filter(
            description__iexact="Issuer WDL Approved NPCI Switching Fee - GST"
        ).first(),
    }

    return render(request, "atm_settlement/detail.html", {
        "cycle": cycle,
        "items": items,
        "summary": summary,
    })