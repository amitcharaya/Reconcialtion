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
from django.db.models.functions import TruncDate

from cbs.models import CBSATMTransaction
from ndpg.models import NDPGATMTransaction
from switchlog.models import SwitchATMTransaction

from reconciliation.models import ATMReconciliationResult
from disputes.models import ATMDisputeCase


MATCHED_STATUSES = [
    "MATCHED_ALL",
    "MATCHED_ONUS",
    "CBS_AUTO_REVERSED",
    "SWITCH_WITHDRAWAL_REVERSED",
    "FAILED_REVERSED_NO_DISPUTE",
    "FAILED_NDPG_ONLY",
    "SWITCH_ONLY_DECLINED",
    "NDPG_SWITCH_ONLY_0_AMOUNT",
    "AUTO_MATCHED_NEXT_DAY_NDPG",

]


class MISDashboardService:

    @staticmethod
    def safe_sum(queryset, field_name):
        return (
            queryset
            .aggregate(total=Sum(field_name))
            .get("total") or Decimal("0.00")
        )

    @staticmethod
    def get_reconciliation_qs(from_date=None, to_date=None):
        qs = ATMReconciliationResult.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__date__lte=to_date)

        return qs

    @staticmethod
    def get_dispute_qs(from_date=None, to_date=None):
        qs = ATMDisputeCase.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def get_cbs_qs(from_date=None, to_date=None):
        qs = CBSATMTransaction.objects.all()

        if from_date:
            qs = qs.filter(txn_date__gte=from_date)

        if to_date:
            qs = qs.filter(txn_date__lte=to_date)

        return qs

    @staticmethod
    def get_ndpg_qs(from_date=None, to_date=None):
        qs = NDPGATMTransaction.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def get_switch_qs(from_date=None, to_date=None):
        qs = SwitchATMTransaction.objects.all()

        if from_date:
            qs = qs.filter(transaction_date__gte=from_date)

        if to_date:
            qs = qs.filter(transaction_date__lte=to_date)

        return qs

    @staticmethod
    def enterprise_summary(from_date=None, to_date=None):
        reconciliation_qs = MISDashboardService.get_reconciliation_qs(
            from_date,
            to_date
        )

        dispute_qs = MISDashboardService.get_dispute_qs(
            from_date,
            to_date
        )

        total_reconciliation = reconciliation_qs.count()

        matched = reconciliation_qs.filter(
            status__in=MATCHED_STATUSES
        ).count()

        unmatched = reconciliation_qs.exclude(
            status__in=MATCHED_STATUSES
        ).count()

        total_disputes = dispute_qs.count()

        open_disputes = dispute_qs.filter(
            case_status="OPEN"
        ).count()

        financial_exposure = (
            dispute_qs
            .filter(case_status="OPEN")
            .aggregate(total=Sum("disputed_amount"))
            .get("total") or Decimal("0.00")
        )

        return {
            "total_reconciliation": total_reconciliation,
            "matched": matched,
            "unmatched": unmatched,
            "total_disputes": total_disputes,
            "open_disputes": open_disputes,
            "financial_exposure": financial_exposure,
        }

    @staticmethod
    def status_summary(from_date=None, to_date=None):
        return list(
            MISDashboardService.get_reconciliation_qs(
                from_date,
                to_date
            )
            .values("status")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

    @staticmethod
    def dispute_status_summary(from_date=None, to_date=None):
        return list(
            MISDashboardService.get_dispute_qs(
                from_date,
                to_date
            )
            .values("case_status")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

    @staticmethod
    def daily_reconciliation_trend(from_date=None, to_date=None):
        return list(
            MISDashboardService.get_reconciliation_qs(
                from_date,
                to_date
            )
            .annotate(day=TruncDate("transaction_date"))
            .values("day")
            .annotate(
                total=Count("id"),
                matched=Count(
                    "id",
                    filter=Q(status__in=MATCHED_STATUSES)
                ),
                unmatched=Count(
                    "id",
                    filter=~Q(status__in=MATCHED_STATUSES)
                ),
            )
            .order_by("day")
        )

    @staticmethod
    def exception_summary(from_date=None, to_date=None):
        return list(
            MISDashboardService.get_reconciliation_qs(
                from_date,
                to_date
            )
            .exclude(status__in=MATCHED_STATUSES)
            .values("status")
            .annotate(
                total=Count("id"),
                cbs_amount=Sum("cbs_amount"),
                ndpg_amount=Sum("ndpg_amount"),
                switch_amount=Sum("switch_amount"),
            )
            .order_by("-total")
        )

    @staticmethod
    def recent_disputes(from_date=None, to_date=None):
        return list(
            MISDashboardService.get_dispute_qs(
                from_date,
                to_date
            )
            .order_by("-created_at")[:10]
        )

    @staticmethod
    def get_issuer_withdrawal_amount(from_date=None, to_date=None):
        """
        Returns total Acquirer Withdrawal Amount for a given settlement date.
        """

        from atm_settlement.models import ATMSettlementCycle, ATMSettlementItem

        # Step 1: Get all cycles for the given date
        cycles = ATMSettlementCycle.objects.filter(settlement_date__gte=from_date, settlement_date__lte=to_date)

        if not cycles.exists():
            return Decimal("0.00")

        # Step 2: Filter settlement items for Acquirer Withdrawal
        result = ATMSettlementItem.objects.filter(
            settlement_cycle__in=cycles,
            description__icontains="Issuer WDL Transaction Amount",
        ).aggregate(
            total_amount=Sum("debit_amount")  # withdrawal is usually debit
        )

        return result["total_amount"] or Decimal("0.00")


    @staticmethod
    def get_acquirer_withdrawal_amount(from_date=None, to_date=None):
        """
        Returns total Acquirer Withdrawal Amount for a given settlement date.
        """

        from atm_settlement.models import ATMSettlementCycle, ATMSettlementItem

        # Step 1: Get all cycles for the given date
        cycles = ATMSettlementCycle.objects.filter(settlement_date__gte=from_date,settlement_date__lte=to_date)

        if not cycles.exists():
            return Decimal("0.00")

        # Step 2: Filter settlement items for Acquirer Withdrawal
        result = ATMSettlementItem.objects.filter(
            settlement_cycle__in=cycles,
            description__icontains="Acquirer WDL Transaction Amount",
        ).aggregate(
            total_amount=Sum("credit_amount")  # withdrawal is usually credit
        )

        return result["total_amount"] or Decimal("0.00")

    @staticmethod
    def source_financial_summary(from_date=None, to_date=None):

        cbs_qs = MISDashboardService.get_cbs_qs(from_date, to_date)
        ndpg_qs = MISDashboardService.get_ndpg_qs(from_date, to_date)
        switch_qs = MISDashboardService.get_switch_qs(from_date, to_date)
        acquirer_wdl_amount=MISDashboardService.get_acquirer_withdrawal_amount(from_date,to_date)
        issuer_wdl_amount=MISDashboardService.get_issuer_withdrawal_amount(from_date,to_date)
        def cbs_summary(file_type):
            debit = MISDashboardService.safe_sum(
                cbs_qs.filter(
                    file_type__iexact=file_type,
                    dr_cr_flag__iexact="D"
                ),
                "txn_amount"
            )

            credit = MISDashboardService.safe_sum(
                cbs_qs.filter(
                    file_type__iexact=file_type,
                    dr_cr_flag__iexact="C"
                ),
                "txn_amount"
            )

            return {
                "debit": debit,
                "credit": credit,
                "net": debit - credit,
            }

        cbs_acquirer = cbs_summary("A")
        cbs_issuer = cbs_summary("I")
        cbs_onus = cbs_summary("O")

        cbs_total_debit = (
            cbs_acquirer["debit"]
            + cbs_issuer["debit"]
            + cbs_onus["debit"]
        )

        cbs_total_credit = (
            cbs_acquirer["credit"]
            + cbs_issuer["credit"]
            + cbs_onus["credit"]
        )

        cbs_total_net = cbs_total_debit - cbs_total_credit

        def ndpg_summary(file_type):
            return MISDashboardService.safe_sum(
                ndpg_qs.filter(
                    file_type__iexact=file_type,
                    response_code="00"
                ),
                "actual_transaction_amount"
            )

        ndpg_acquirer = ndpg_summary("ACQUIRER")
        ndpg_issuer = ndpg_summary("ISSUER")

        ndpg_total = ndpg_acquirer + ndpg_issuer

        def switch_success_summary(interface_type):
            return MISDashboardService.safe_sum(
                switch_qs.filter(
                    interface_type__iexact=interface_type,
                    void_code="0",
                    transaction_type__iexact="Withdrawal"
                ),
                "transaction_amount"
            )

        def switch_reversal_summary(interface_type):
            return MISDashboardService.safe_sum(
                switch_qs.filter(
                    interface_type__iexact=interface_type,
                    transaction_type__iexact="Withdrawal Reversal"
                ),
                "transaction_amount"
            )

        switch_acquirer_success = switch_success_summary("ACQUIRER")
        switch_issuer_success = switch_success_summary("ISSUER")
        switch_onus_success = switch_success_summary("ONUS")

        switch_acquirer_reversal = switch_reversal_summary("ACQUIRER")
        switch_issuer_reversal = switch_reversal_summary("ISSUER")
        switch_onus_reversal = switch_reversal_summary("ONUS")

        switch_acquirer_net = switch_acquirer_success - switch_acquirer_reversal
        switch_issuer_net = switch_issuer_success - switch_issuer_reversal
        switch_onus_net = switch_onus_success - switch_onus_reversal

        switch_total_success = (
            switch_acquirer_success
            + switch_issuer_success
            + switch_onus_success
        )

        switch_total_reversal = (
            switch_acquirer_reversal
            + switch_issuer_reversal
            + switch_onus_reversal
        )

        switch_total_net = switch_total_success - switch_total_reversal



        return {
            "cbs": {
                "acquirer": cbs_acquirer,
                "issuer": cbs_issuer,
                "onus": cbs_onus,
                "total": {
                    "debit": cbs_total_debit,
                    "credit": cbs_total_credit,
                    "net": cbs_total_net,
                },
            },

            "ndpg": {
                "acquirer": ndpg_acquirer,
                "issuer": ndpg_issuer,
                "total": ndpg_total,
            },

            "switch": {
                "acquirer": {
                    "success": switch_acquirer_success,
                    "reversal": switch_acquirer_reversal,
                    "net": switch_acquirer_net,
                },
                "issuer": {
                    "success": switch_issuer_success,
                    "reversal": switch_issuer_reversal,
                    "net": switch_issuer_net,
                },
                "onus": {
                    "success": switch_onus_success,
                    "reversal": switch_onus_reversal,
                    "net": switch_onus_net,
                },
                "total": {
                    "success": switch_total_success,
                    "reversal": switch_total_reversal,
                    "net": switch_total_net,
                },
            },

            "difference": {
                "cbs_ndpg_acquirer": cbs_acquirer["net"] - ndpg_acquirer,
                "cbs_ndpg_issuer": cbs_issuer["net"] - ndpg_issuer,
                "cbs_ndpg_onus": cbs_onus["net"] - switch_onus_net,
                "cbs_ndpg_total": (
                    cbs_total_net
                    - ndpg_total
                    - switch_onus_net
                ),
            },
            "ntsl":{
                "acquirer": acquirer_wdl_amount,
                "issuer": issuer_wdl_amount,
            }
        }

class MISDashboardFilterService:

        @staticmethod
        def filtered_reconciliation_queryset(
                from_date=None,
                to_date=None,
                status=None,
                stan=None,
                rrn=None,
        ):
            qs = ATMReconciliationResult.objects.all()

            if from_date:
                qs = qs.filter(transaction_date__date__gte=from_date)

            if to_date:
                qs = qs.filter(transaction_date__date__lte=to_date)

            if status:
                qs = qs.filter(status=status)

            if stan:
                qs = qs.filter(stan_no__icontains=stan)

            if rrn:
                qs = qs.filter(rrn__icontains=rrn)

            return qs

        @staticmethod
        def filtered_dispute_queryset(
                from_date=None,
                to_date=None,
                case_status=None,
                stan=None,
                rrn=None,
        ):
            qs = ATMDisputeCase.objects.all()

            if from_date:
                qs = qs.filter(transaction_date__gte=from_date)

            if to_date:
                qs = qs.filter(transaction_date__lte=to_date)

            if case_status:
                qs = qs.filter(case_status=case_status)

            if stan:
                qs = qs.filter(stan_no__icontains=stan)

            if rrn:
                qs = qs.filter(rrn__icontains=rrn)

            return qs