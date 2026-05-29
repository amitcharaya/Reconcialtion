from django.db import models
from decimal import Decimal


class ATMSettlementCycle(models.Model):
    settlement_date = models.DateField()
    cycle_no = models.CharField(max_length=10)

    original_filename = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to="atm_settlement/")

    issuer_sub_total = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    acquirer_sub_total = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))

    settlement_amount = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    net_adjusted_amount = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    final_settlement_amount = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("settlement_date", "cycle_no")

    def __str__(self):
        return f"ATM Settlement {self.settlement_date} - {self.cycle_no}"


class ATMSettlementItem(models.Model):
    settlement_cycle = models.ForeignKey(
        ATMSettlementCycle,
        on_delete=models.CASCADE,
        related_name="items"
    )

    description = models.CharField(max_length=300)
    txn_count = models.IntegerField(default=0)

    debit_amount = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    credit_amount = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))

    def __str__(self):
        return f"{self.description} - {self.settlement_cycle}"