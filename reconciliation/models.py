"""
Data model definitions for the reconciliation application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models


class ATMReconciliationResult(models.Model):

    STATUS_CHOICES = [
        ("MATCHED_ALL", "Matched in All Sources"),
        ("CBS_ONLY", "CBS Only"),
        ("NDPG_ONLY", "NDPG Only"),
        ("SWITCH_ONLY", "Switch Only"),
        ("CBS_NDPG_ONLY", "CBS and NDPG Only"),
        ("CBS_SWITCH_ONLY", "CBS and Switch Only"),
        ("NDPG_SWITCH_ONLY", "NDPG and Switch Only"),
        ("CBS_AUTO_REVERSED", "CBS Auto Reversed"),
        ("SWITCH_WITHDRAWAL_REVERSED", "Switch Withdrawal Reversed"),
        ("FAILED_REVERSED_NO_DISPUTE", "Failed / Reversed - No Dispute"),
        ("AMOUNT_MISMATCH", "Amount Mismatch"),
        ("FAILED_NDPG_ONLY", "Failed Txns NDPG Only"),
        ("NDPG_SWITCH_ONLY_0_AMOUNT", "NDPG Switch Only Zero Amount"),
        ("SWITCH_ONLY_DECLINED", "Switch Only Declined"),
        ("MATCHED_ONUS", "Matched On-Us"),
        ("PENDING_NDPG_NEXT_DAY", "Pending NDPG Next Day Settlement"),
        ("AUTO_MATCHED_NEXT_DAY_NDPG", "Auto Matched with Next Day NDPG"),
    ]

    transaction_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    stan_no = models.CharField(max_length=20, blank=True, null=True)
    rrn = models.CharField(max_length=30, blank=True, null=True)

    cbs_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )

    ndpg_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )

    switch_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )

    cbs_present = models.BooleanField(default=False)
    ndpg_present = models.BooleanField(default=False)
    switch_present = models.BooleanField(default=False)

    matched_by = models.CharField(max_length=50, blank=True, null=True)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES
    )

    remarks = models.TextField(blank=True, null=True)

    reconciled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_date} - {self.stan_no or self.rrn} - {self.status}"