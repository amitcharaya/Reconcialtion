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
    """
    Central workflow builder for MIS dashboard.

    This service evaluates:
    - Upload status of CBS, Switch, NDPG
    - Reconciliation status
    - Next actionable step for user

    It returns a structured response used by UI/dashboard.
    """

    # Configuration-driven product definition
    # This allows easy extension without modifying logic
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
        """
               Checks whether ATM upload exists for a given source and date.

               Business rules:
               - CBS must be SUCCESS
               - Switch & NDPG only require existence
               """
        if source == "CBS":
            return UploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists()
        if source == "SWITCH":
            return SwitchLogUploadBatch.objects.filter(upload_date=selected_date).exists()
        if source == "NDPG":
            return NDPGUploadBatch.objects.filter(upload_date=selected_date).exists()
        return False

    @staticmethod
    def _has_rgcs(source, selected_date):
        """
                RGCS allows PARTIAL uploads due to multi-file or delayed settlement inputs.
                """
        if source == "CBS":
            return CBSRGCSUploadBatch.objects.filter(batch_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        if source == "SWITCH":
            return RGCSSwitchUploadBatch.objects.filter(batch_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        if source == "NDPG":
            return NDPGRGCSUploadBatch.objects.filter(batch_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        return False

    @staticmethod
    def _has_imps(source, selected_date):
        """
               IMPS upload validation:
               - CBS & Switch require SUCCESS
               - NDPG allows PARTIAL due to raw file nature
               """
        if source == "CBS":
            return CBSIMPSUploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists()
        if source == "SWITCH":
            return SwitchIMPSUploadBatch.objects.filter(batch_date=selected_date, upload_status="SUCCESS").exists()
        if source == "NDPG":
            return NDPGIMPSRawUploadBatch.objects.filter(file_date=selected_date, upload_status__in=["SUCCESS", "PARTIAL"]).exists()
        return False

    @staticmethod
    def _is_reconciled(product_key, selected_date):
        """
               Checks whether reconciliation has already been executed.

               Important:
               ATM uses datetime field, others use date field.
               """
        if product_key == "ATM":
            return ATMReconciliationResult.objects.filter(transaction_date__date=selected_date).exists()
        if product_key == "RGCS":
            return RGCSReconciliationResult.objects.filter(transaction_date=selected_date).exists()
        if product_key == "IMPS":
            return IMPSReconciliationResult.objects.filter(transaction_date=selected_date).exists()
        return False

    @staticmethod
    def _has_upload(product_key, source, selected_date):
        """
                Delegates upload check to product-specific logic.

                Keeps build() method clean and maintainable.
                """
        if product_key == "ATM":
            return UploadWorkflowService._has_atm(source, selected_date)
        if product_key == "RGCS":
            return UploadWorkflowService._has_rgcs(source, selected_date)
        if product_key == "IMPS":
            return UploadWorkflowService._has_imps(source, selected_date)
        return False

    @staticmethod
    def build(selected_date=None):
        """
               Core workflow builder.

               Steps:
               1. Determine upload completion per source
               2. Evaluate reconciliation status
               3. Generate next action message
               4. Return structured workflow for UI
               """
        selected_date = selected_date or date.today()
        workflows = []

        for product in UploadWorkflowService.PRODUCTS:
            # Track individual upload steps
            upload_steps = []
            # Count completed uploads (CBS, Switch, NDPG)
            completed_count = 0

            for source, url_name in product["uploads"]:
                # Check upload completion
                completed = UploadWorkflowService._has_upload(product["key"], source, selected_date)
                # Increment counter if completed
                completed_count += 1 if completed else 0
                # Build upload step metadata for UI
                upload_steps.append({
                    "source": source,
                    "completed": completed,
                    # Dynamic URL with query params
                    "url": reverse(url_name) + f"?transaction_date={selected_date}&batch_date={selected_date}&upload_date={selected_date}",
                    "status_text": "Uploaded" if completed else "Pending",
                })
            # Identify pending uploads
            pending_steps = [step for step in upload_steps if not step["completed"]]
            # Check overall completion
            all_uploaded = completed_count == 3
            # Check reconciliation status
            reconciled = UploadWorkflowService._is_reconciled(product["key"], selected_date)
            # Determine next action for user
            if all_uploaded and reconciled:
                next_action = "All files uploaded and reconciliation completed for this date."
            elif all_uploaded:
                next_action = "All three files are uploaded. You can start reconciliation."
            elif completed_count == 0:
                next_action = "Start by uploading CBS, Switch or NDPG file for this date."
            else:
                left = ", ".join(step["source"] for step in pending_steps)
                next_action = f"Upload pending source(s): {left}."
            # Final workflow object for UI
            workflows.append({
                "key": product["key"],
                "title": product["title"],
                "steps": upload_steps,
                "completed_count": completed_count,
                "all_uploaded": all_uploaded,
                "reconciled": reconciled,
                "next_action": next_action,
                # Dashboard navigation
                "dashboard_url": reverse(product["dashboard_url"]) + f"?from_date={selected_date}&to_date={selected_date}",
                # Reconciliation trigger URL
                "reconcile_url": reverse(product["reconcile_url"]) + f"?transaction_date={selected_date}",
            })

        return workflows
