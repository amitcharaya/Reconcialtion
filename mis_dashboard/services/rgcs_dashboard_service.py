"""
Service-layer business logic for the mis_dashboard application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from decimal import Decimal

from django.db.models import Count, Sum, Q

from cbs.models import RGCSCBSTransaction, RGCSUploadBatch as CBSRGCSUploadBatch
from switchlog.models import RGCSSwitchTransaction, RGCSSwitchUploadBatch
from ndpg.models import RGCSRawTransaction, RGCSUploadBatch as NDPGRGCSUploadBatch
from rgcs_reconciliation.models import RGCSReconciliationResult
from disputes.models import RGCSDisputeCase


RGCS_MATCHED_STATUSES = ["MATCHED"]


class RGCSDashboardService:

    @staticmethod
    def safe_sum(qs, field_name):
        return qs.aggregate(total=Sum(field_name)).get("total") or Decimal("0.00")

    @staticmethod
    def get_cbs_qs(from_date=None, to_date=None):
        qs = RGCSCBSTransaction.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def get_switch_qs(from_date=None, to_date=None):
        qs = RGCSSwitchTransaction.objects.all()

        if from_date:
            qs = qs.filter(tranx_date__gte=from_date)

        if to_date:
            qs = qs.filter(tranx_date__lte=to_date)

        return qs

    @staticmethod
    def get_ndpg_qs(from_date=None, to_date=None):
        qs = RGCSRawTransaction.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def get_recon_qs(from_date=None, to_date=None):
        qs = RGCSReconciliationResult.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def get_dispute_qs(from_date=None, to_date=None):
        qs = RGCSDisputeCase.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def enterprise_summary(from_date=None, to_date=None):
        cbs_qs = RGCSDashboardService.get_cbs_qs(from_date, to_date)
        switch_qs = RGCSDashboardService.get_switch_qs(from_date, to_date)
        ndpg_qs = RGCSDashboardService.get_ndpg_qs(from_date, to_date)
        recon_qs = RGCSDashboardService.get_recon_qs(from_date, to_date)
        dispute_qs = RGCSDashboardService.get_dispute_qs(from_date, to_date)

        total_reconciled = recon_qs.count()

        matched = recon_qs.filter(
            status__in=RGCS_MATCHED_STATUSES
        ).count()

        unmatched = recon_qs.exclude(
            status__in=RGCS_MATCHED_STATUSES
        ).count()

        exposure = (
            dispute_qs
            .filter(case_status="OPEN")
            .aggregate(total=Sum("disputed_amount"))
            .get("total") or Decimal("0.00")
        )

        return {
            "cbs_count": cbs_qs.count(),
            "switch_count": switch_qs.count(),
            "ndpg_count": ndpg_qs.count(),
            "total_reconciled": total_reconciled,
            "matched": matched,
            "unmatched": unmatched,
            "financial_exposure": exposure,
            "total_disputes": dispute_qs.count(),
            "open_disputes": dispute_qs.filter(case_status="OPEN").count(),

            "cbs_amount": RGCSDashboardService.safe_sum(
                cbs_qs,
                "transaction_amount"
            ),

            "switch_amount": RGCSDashboardService.safe_sum(
                switch_qs,
                "amount_approved"
            ),

            "ndpg_amount": RGCSDashboardService.safe_sum(
                ndpg_qs,
                "transaction_amount"
            ),
        }

    @staticmethod
    def status_summary(from_date=None, to_date=None):
        return list(
            RGCSDashboardService.get_recon_qs(from_date, to_date)
            .values("status")
            .annotate(
                total=Count("id"),
                cbs_amount=Sum("cbs_amount"),
                switch_amount=Sum("switch_amount"),
                ndpg_amount=Sum("ndpg_amount"),
            )
            .order_by("-total")
        )

    @staticmethod
    def upload_summary(from_date=None, to_date=None):
        cbs_batches = CBSRGCSUploadBatch.objects.all()
        switch_batches = RGCSSwitchUploadBatch.objects.all()
        ndpg_batches = NDPGRGCSUploadBatch.objects.all()

        if from_date:
            cbs_batches = cbs_batches.filter(batch_date__gte=from_date)
            switch_batches = switch_batches.filter(batch_date__gte=from_date)
            ndpg_batches = ndpg_batches.filter(batch_date__gte=from_date)

        if to_date:
            cbs_batches = cbs_batches.filter(batch_date__lte=to_date)
            switch_batches = switch_batches.filter(batch_date__lte=to_date)
            ndpg_batches = ndpg_batches.filter(batch_date__lte=to_date)

        return {
            "cbs_uploads": cbs_batches.count(),
            "switch_uploads": switch_batches.count(),
            "ndpg_uploads": ndpg_batches.count(),

            "cbs_records": cbs_batches.aggregate(
                total=Sum("total_records")
            ).get("total") or 0,

            "switch_records": switch_batches.aggregate(
                total=Sum("total_records")
            ).get("total") or 0,

            "ndpg_records": ndpg_batches.aggregate(
                total=Sum("total_records")
            ).get("total") or 0,
        }

    @staticmethod
    def filtered_reconciliation_queryset(
        from_date=None,
        to_date=None,
        status=None,
        rrn=None,
    ):
        qs = RGCSReconciliationResult.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        if status:
            qs = qs.filter(status=status)

        if rrn:
            qs = qs.filter(rrn__icontains=rrn)

        return qs
    @staticmethod
    def dispute_status_summary(from_date=None, to_date=None):
        return list(
            RGCSDashboardService.get_dispute_qs(from_date, to_date)
            .values("case_status")
            .annotate(total=Count("id"), amount=Sum("disputed_amount"))
            .order_by("case_status")
        )

    @staticmethod
    def recent_disputes(from_date=None, to_date=None):
        return list(
            RGCSDashboardService.get_dispute_qs(from_date, to_date)
            .order_by("-created_at")[:10]
        )
