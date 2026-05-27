"""
Service-layer business logic for the mis_dashboard application. Keeping this code outside views makes reconciliation, import, and dashboard logic easier to test and maintain.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from itertools import chain
from operator import itemgetter

from django.db.models import Sum

from cbs.models import UploadBatch, CBSIMPSUploadBatch, RGCSUploadBatch as CBSRGCSUploadBatch
from switchlog.models import (
    SwitchLogUploadBatch,
    SwitchIMPSUploadBatch,
    RGCSSwitchUploadBatch,
)
from ndpg.models import (
    NDPGUploadBatch,
    NDPGIMPSRawUploadBatch,
    RGCSUploadBatch as NDPGRGCSUploadBatch,
)


class UploadDashboardService:

    @staticmethod
    def safe_sum(qs, field_name):
        return qs.aggregate(total=Sum(field_name)).get("total") or 0

    @staticmethod
    def build_record(
        source,
        report_type,
        batch_date,
        file_name,
        total_records=0,
        total_errors=0,
        upload_status="SUCCESS",
        remarks="",
        uploaded_at=None,
    ):
        return {
            "source": source,
            "report_type": report_type,
            "batch_date": batch_date,
            "file_name": file_name or "-",
            "total_records": total_records or 0,
            "total_errors": total_errors or 0,
            "success_records": (total_records or 0) - (total_errors or 0),
            "upload_status": upload_status or "SUCCESS",
            "remarks": remarks or "",
            "uploaded_at": uploaded_at,
        }

    @staticmethod
    def get_upload_records(from_date=None, to_date=None):
        records = []

        # CBS ATM
        cbs_atm = UploadBatch.objects.all()
        if from_date:
            cbs_atm = cbs_atm.filter(batch_date__gte=from_date)
        if to_date:
            cbs_atm = cbs_atm.filter(batch_date__lte=to_date)

        for batch in cbs_atm:
            records.append(
                UploadDashboardService.build_record(
                    source="CBS",
                    report_type="ATM CBS",
                    batch_date=batch.batch_date,
                    file_name=f"{batch.acquirer_filename}, {batch.issuer_filename}, {batch.onus_filename}",
                    total_records=batch.total_records,
                    total_errors=batch.total_errors,
                    upload_status=batch.upload_status,
                    remarks=batch.remarks,
                    uploaded_at=batch.uploaded_at,
                )
            )

        # CBS IMPS
        cbs_imps = CBSIMPSUploadBatch.objects.all()
        if from_date:
            cbs_imps = cbs_imps.filter(batch_date__gte=from_date)
        if to_date:
            cbs_imps = cbs_imps.filter(batch_date__lte=to_date)

        for batch in cbs_imps:
            records.append(
                UploadDashboardService.build_record(
                    source="CBS",
                    report_type="IMPS CBS",
                    batch_date=batch.batch_date,
                    file_name=f"{batch.acquirer_filename}, {batch.issuer_filename}, {batch.onus_filename}",
                    total_records=batch.total_records,
                    total_errors=batch.total_errors,
                    upload_status=batch.upload_status,
                    remarks=batch.remarks,
                    uploaded_at=batch.uploaded_at,
                )
            )

        # CBS RGCS
        cbs_rgcs = CBSRGCSUploadBatch.objects.all()
        if from_date:
            cbs_rgcs = cbs_rgcs.filter(batch_date__gte=from_date)
        if to_date:
            cbs_rgcs = cbs_rgcs.filter(batch_date__lte=to_date)

        for batch in cbs_rgcs:
            records.append(
                UploadDashboardService.build_record(
                    source="CBS",
                    report_type="RGCS CBS",
                    batch_date=batch.batch_date,
                    file_name=batch.source_filename,
                    total_records=batch.total_records,
                    total_errors=batch.total_errors,
                    upload_status=batch.upload_status,
                    remarks=batch.remarks,
                    uploaded_at=batch.uploaded_at,
                )
            )

        # Switch ATM
        switch_atm = SwitchLogUploadBatch.objects.all()
        if from_date:
            switch_atm = switch_atm.filter(upload_date__gte=from_date)
        if to_date:
            switch_atm = switch_atm.filter(upload_date__lte=to_date)

        for batch in switch_atm:
            records.append(
                UploadDashboardService.build_record(
                    source="SWITCH",
                    report_type="ATM Switch",
                    batch_date=batch.upload_date,
                    file_name=batch.filename,
                    total_records=batch.total_records,
                    total_errors=0,
                    upload_status="SUCCESS",
                    uploaded_at=batch.uploaded_at,
                )
            )

        # Switch IMPS
        switch_imps = SwitchIMPSUploadBatch.objects.all()
        if from_date:
            switch_imps = switch_imps.filter(batch_date__gte=from_date)
        if to_date:
            switch_imps = switch_imps.filter(batch_date__lte=to_date)

        for batch in switch_imps:
            records.append(
                UploadDashboardService.build_record(
                    source="SWITCH",
                    report_type="IMPS Switch",
                    batch_date=batch.batch_date,
                    file_name=batch.filename,
                    total_records=batch.total_records,
                    total_errors=batch.total_errors,
                    upload_status=batch.upload_status,
                    remarks=batch.remarks,
                    uploaded_at=batch.uploaded_at,
                )
            )

        # Switch RGCS
        switch_rgcs = RGCSSwitchUploadBatch.objects.all()
        if from_date:
            switch_rgcs = switch_rgcs.filter(batch_date__gte=from_date)
        if to_date:
            switch_rgcs = switch_rgcs.filter(batch_date__lte=to_date)

        for batch in switch_rgcs:
            records.append(
                UploadDashboardService.build_record(
                    source="SWITCH",
                    report_type="RGCS Switch",
                    batch_date=batch.batch_date,
                    file_name=batch.source_filename,
                    total_records=batch.total_records,
                    total_errors=batch.total_errors,
                    upload_status=batch.upload_status,
                    remarks=batch.remarks,
                    uploaded_at=batch.uploaded_at,
                )
            )

        # NDPG ATM
        ndpg_atm = NDPGUploadBatch.objects.all()
        if from_date:
            ndpg_atm = ndpg_atm.filter(upload_date__gte=from_date)
        if to_date:
            ndpg_atm = ndpg_atm.filter(upload_date__lte=to_date)

        for batch in ndpg_atm:
            file_names = [
                batch.cycle_1_acquirer_filename,
                batch.cycle_1_issuer_filename,
                batch.cycle_2_acquirer_filename,
                batch.cycle_2_issuer_filename,
                batch.cycle_3_acquirer_filename,
                batch.cycle_3_issuer_filename,
                batch.cycle_4_acquirer_filename,
                batch.cycle_4_issuer_filename,
            ]

            records.append(
                UploadDashboardService.build_record(
                    source="NDPG",
                    report_type="ATM NDPG",
                    batch_date=batch.upload_date,
                    file_name=", ".join(file_names),
                    total_records=batch.total_records,
                    total_errors=0,
                    upload_status="SUCCESS",
                    uploaded_at=batch.uploaded_at,
                )
            )

        # NDPG IMPS
        ndpg_imps = NDPGIMPSRawUploadBatch.objects.all()
        if from_date:
            ndpg_imps = ndpg_imps.filter(file_date__gte=from_date)
        if to_date:
            ndpg_imps = ndpg_imps.filter(file_date__lte=to_date)

        for batch in ndpg_imps:
            records.append(
                UploadDashboardService.build_record(
                    source="NDPG",
                    report_type=f"IMPS NDPG {batch.file_type} Cycle {batch.cycle_no}",
                    batch_date=batch.file_date,
                    file_name=batch.source_filename,
                    total_records=batch.total_records,
                    total_errors=batch.skipped_records,
                    upload_status=batch.upload_status,
                    remarks=batch.error_message,
                    uploaded_at=batch.uploaded_at,
                )
            )

        # NDPG RGCS
        ndpg_rgcs = NDPGRGCSUploadBatch.objects.all()
        if from_date:
            ndpg_rgcs = ndpg_rgcs.filter(batch_date__gte=from_date)
        if to_date:
            ndpg_rgcs = ndpg_rgcs.filter(batch_date__lte=to_date)

        for batch in ndpg_rgcs:
            file_names = [
                batch.file_861,
                batch.file_862,
                batch.file_863,
                batch.file_864,
            ]

            records.append(
                UploadDashboardService.build_record(
                    source="NDPG",
                    report_type=f"RGCS NDPG {batch.record_nature}",
                    batch_date=batch.batch_date,
                    file_name=", ".join([x for x in file_names if x]),
                    total_records=batch.total_records,
                    total_errors=batch.total_errors,
                    upload_status=batch.upload_status,
                    remarks=batch.remarks,
                    uploaded_at=batch.uploaded_at,
                )
            )

        return sorted(
            records,
            key=lambda x: x["uploaded_at"] or x["batch_date"],
            reverse=True,
        )

    @staticmethod
    def upload_summary(from_date=None, to_date=None):
        records = UploadDashboardService.get_upload_records(from_date, to_date)

        return {
            "total_uploads": len(records),
            "success_uploads": len([r for r in records if r["upload_status"] == "SUCCESS"]),
            "failed_uploads": len([r for r in records if r["upload_status"] == "FAILED"]),
            "partial_uploads": len([r for r in records if r["upload_status"] == "PARTIAL"]),
            "total_records": sum(r["total_records"] for r in records),
            "total_errors": sum(r["total_errors"] for r in records),
            "success_records": sum(r["success_records"] for r in records),
        }

    @staticmethod
    def source_summary(from_date=None, to_date=None):
        records = UploadDashboardService.get_upload_records(from_date, to_date)

        summary = {}

        for record in records:
            source = record["source"]

            if source not in summary:
                summary[source] = {
                    "source": source,
                    "total_uploads": 0,
                    "total_records": 0,
                    "total_errors": 0,
                    "success_records": 0,
                }

            summary[source]["total_uploads"] += 1
            summary[source]["total_records"] += record["total_records"]
            summary[source]["total_errors"] += record["total_errors"]
            summary[source]["success_records"] += record["success_records"]

        return list(summary.values())

    @staticmethod
    def recent_uploads(limit=20):
        return UploadDashboardService.get_upload_records()[:limit]