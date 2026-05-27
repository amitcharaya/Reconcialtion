"""
Data model definitions for the rgcs_reconciliation application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models


class RGCSReconciliationResult(models.Model):

    STATUS_CHOICES = [
        ("MATCHED", "Matched"),
        ("CBS_ONLY", "CBS Only"),
        ("NDPG_ONLY", "NDPG Only"),
        ("SWITCH_ONLY", "Switch Only"),
        ("CBS_NDPG_ONLY", "CBS + NDPG Only"),
        ("CBS_SWITCH_ONLY", "CBS + Switch Only"),
        ("NDPG_SWITCH_ONLY", "NDPG + Switch Only"),
        ("AMOUNT_MISMATCH", "Amount Mismatch"),
    ]

    transaction_date = models.DateField()
    rrn = models.CharField(max_length=30)

    cbs_transaction_id = models.IntegerField(null=True, blank=True)
    ndpg_transaction_id = models.IntegerField(null=True, blank=True)
    switch_transaction_id = models.IntegerField(null=True, blank=True)

    cbs_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ndpg_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    switch_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True, null=True)

    reconciled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("transaction_date", "rrn")
        ordering = ["-transaction_date", "rrn"]

    def __str__(self):
        return f"{self.transaction_date} - {self.rrn} - {self.status}"