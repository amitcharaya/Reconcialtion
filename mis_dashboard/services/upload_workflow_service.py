"""
Service-layer business logic for the mis_dashboard application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from datetime import date
from django.urls import reverse

from cbs.models import UploadBatch, CBSIMPSUploadBatch, RGCSUploadBatch as CBSRGCSUploadBatch
from switchlog.models import SwitchLogUploadBatch, SwitchIMPSUploadBatch, RGCSSwitchUploadBatch
from ndpg.models import NDPGUploadBatch, NDPGIMPSRawUploadBatch, RGCSUploadBatch as NDPGRGCSUploadBatch
from reconciliation.models import ATMReconciliationResult
from imps_reconciliation.models import IMPSReconciliationResult
from rgcs_reconciliation.models import RGCSReconciliationResult


# Central service used by the home page to decide which upload step is pending
# for ATM, RGCS, and IMPS on a selected business date.
class UploadWorkflowService:
    """Builds the home-page workflow status for ATM, RGCS and IMPS datewise uploads."""

    PRODUCTS = [
        {
            "key": "ATM",
            "title": "ATM Reconciliation",
            "dashboard_url": "mis_dashboard:dashboard",
            "reconcile_url": "reconcile_atm",
            "uploads": [
                ("CBS", "upload_cbs"),
                ("SWITCH", "upload_switch_log"),
                ("NDPG", "upload_ndpg"),
            ],
        },
        {
            "key": "RGCS",
            "title": "RGCS Reconciliation",
            "dashboard_url": "mis_dashboard:rgcs_dashboard",
            "reconcile_url": "rgcs_reconciliation:run_rgcs_reconciliation",
            "uploads": [
                ("CBS", "upload_rgcs_cbs_file"),
                ("SWITCH", "upload_rgcs_switch_file"),
                ("NDPG", "upload_rgcs_raw_files"),
            ],
        },
        {
            "key": "IMPS",
            "title": "IMPS Reconciliation",
            "dashboard_url": "imps_reconciliation:imps_mis_report",
            "reconcile_url": "imps_reconciliation:run_imps_reconciliation",
            "uploads": [
                ("CBS", "upload_cbs_imps"),
                ("SWITCH", "upload_switch_imps"),
                ("NDPG", "upload_imps_raw"),
            ],
        },
    ]

    @staticmethod
    def _has_atm(source, selected_date):
        if source == "CBS":
            return UploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists()
        if source == "SWITCH":
            return SwitchLogUploadBatch.objects.filter(upload_date=selected_date).exists()
        if source == "NDPG":
            return NDPGUploadBatch.objects.filter(upload_date=selected_date).exists()
        return False

    @staticmethod
    def _has_rgcs(source, selected_date):
        if source == "CBS":
            return CBSRGCSUploadBatch.objects.filter(batch_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        if source == "SWITCH":
            return RGCSSwitchUploadBatch.objects.filter(batch_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        if source == "NDPG":
            return NDPGRGCSUploadBatch.objects.filter(batch_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        return False

    @staticmethod
    def _has_imps(source, selected_date):
        if source == "CBS":
            return CBSIMPSUploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists()
        if source == "SWITCH":
            return SwitchIMPSUploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists()
        if source == "NDPG":
            return NDPGIMPSRawUploadBatch.objects.filter(file_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        return False

    @staticmethod
    def _is_reconciled(product_key, selected_date):
        if product_key == "ATM":
            return ATMReconciliationResult.objects.filter(transaction_date__date=selected_date).exists()
        if product_key == "RGCS":
            return RGCSReconciliationResult.objects.filter(transaction_date=selected_date).exists()
        if product_key == "IMPS":
            return IMPSReconciliationResult.objects.filter(transaction_date=selected_date).exists()
        return False

    @staticmethod
    def _has_upload(product_key, source, selected_date):
        if product_key == "ATM":
            return UploadWorkflowService._has_atm(source, selected_date)
        if product_key == "RGCS":
            return UploadWorkflowService._has_rgcs(source, selected_date)
        if product_key == "IMPS":
            return UploadWorkflowService._has_imps(source, selected_date)
        return False

    @staticmethod
    def build(selected_date=None):
        selected_date = selected_date or date.today()
        workflows = []

        for product in UploadWorkflowService.PRODUCTS:
            upload_steps = []
            completed_count = 0

            for source, url_name in product["uploads"]:
                completed = UploadWorkflowService._has_upload(product["key"], source, selected_date)
                completed_count += 1 if completed else 0
                upload_steps.append({
                    "source": source,
                    "completed": completed,
                    "url": reverse(url_name) + f"?transaction_date={selected_date}&batch_date={selected_date}&upload_date={selected_date}",
                    "status_text": "Uploaded" if completed else "Pending",
                })

            pending_steps = [step for step in upload_steps if not step["completed"]]
            all_uploaded = completed_count == 3
            reconciled = UploadWorkflowService._is_reconciled(product["key"], selected_date)

            if all_uploaded and reconciled:
                next_action = "All files uploaded and reconciliation completed for this date."
            elif all_uploaded:
                next_action = "All three files are uploaded. You can start reconciliation."
            elif completed_count == 0:
                next_action = "Start by uploading CBS, Switch or NDPG file for this date."
            else:
                left = ", ".join(step["source"] for step in pending_steps)
                next_action = f"Upload pending source(s): {left}."

            workflows.append({
                "key": product["key"],
                "title": product["title"],
                "steps": upload_steps,
                "completed_count": completed_count,
                "all_uploaded": all_uploaded,
                "reconciled": reconciled,
                "next_action": next_action,
                "dashboard_url": reverse(product["dashboard_url"]) + f"?from_date={selected_date}&to_date={selected_date}",
                "reconcile_url": reverse(product["reconcile_url"]) + f"?transaction_date={selected_date}",
            })

        return workflows
