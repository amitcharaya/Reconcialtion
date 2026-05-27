"""
Data model definitions for the imps_reconciliation application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models


class IMPSReconciliationResult(models.Model):

    STATUS_CHOICES = [
        ("MATCHED_ALL", "Matched in CBS, Switch and NDPG"),
        ("CBS_ONLY", "CBS Only"),
        ("SWITCH_ONLY", "Switch Only"),
        ("NDPG_ONLY", "NDPG Only"),
        ("CBS_SWITCH_ONLY", "CBS and Switch Only"),
        ("CBS_NDPG_ONLY", "CBS and NDPG Only"),
        ("SWITCH_NDPG_ONLY", "Switch and NDPG Only"),
        ("AMOUNT_MISMATCH", "Amount Mismatch"),
        ("FAILED_NDPG_ONLY", "Failed NDPG Only"),
        ("CBS_AUTO_REVERSED", "CBS Auto Reversed"),
    ]

    transaction_date = models.DateField(db_index=True)

    cbs_transaction = models.ForeignKey(
        "cbs.CBSIMPSTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imps_reconciliation_results"
    )

    switch_transaction = models.ForeignKey(
        "switchlog.SwitchIMPSTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imps_reconciliation_results"
    )

    ndpg_transaction = models.ForeignKey(
        "ndpg.NDPGIMPSRawTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imps_reconciliation_results"
    )

    transaction_serial_number = models.CharField(max_length=50, db_index=True)

    rrn = models.CharField(max_length=50, blank=True, null=True, db_index=True)

    cbs_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    switch_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ndpg_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, db_index=True)

    reason = models.TextField(blank=True, null=True)

    reconciled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "transaction_date",
            "transaction_serial_number",
            "status",
        )

    def __str__(self):
        return f"{self.transaction_serial_number} - {self.status}"