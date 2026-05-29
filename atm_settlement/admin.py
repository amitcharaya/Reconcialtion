from django.contrib import admin
from .models import ATMSettlementCycle, ATMSettlementItem


class ATMSettlementItemInline(admin.TabularInline):
    model = ATMSettlementItem
    extra = 0


@admin.register(ATMSettlementCycle)
class ATMSettlementCycleAdmin(admin.ModelAdmin):
    list_display = (
        "settlement_date",
        "cycle_no",
        "issuer_sub_total",
        "acquirer_sub_total",
        "settlement_amount",
        "final_settlement_amount",
    )
    list_filter = ("settlement_date", "cycle_no")
    inlines = [ATMSettlementItemInline]


@admin.register(ATMSettlementItem)
class ATMSettlementItemAdmin(admin.ModelAdmin):
    list_display = (
        "settlement_cycle",
        "description",
        "txn_count",
        "debit_amount",
        "credit_amount",
    )
    search_fields = ("description",)