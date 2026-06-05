"""
Data model definitions for the disputes application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models

class ATMDisputeCase(models.Model):
    transaction_date = models.DateField()

    stan_no = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    rrn = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    account_no = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    disputed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )

    source_status = models.CharField(
        max_length=50
    )

    dispute_reason = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    case_status = models.CharField(
        max_length=30,
        default="OPEN"
    )

    assigned_to = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )



class RGCSDisputeCase(models.Model):
    transaction_date = models.DateField(db_index=True)
    rrn = models.CharField(max_length=30, db_index=True)
    disputed_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    source_status = models.CharField(max_length=50, db_index=True)
    dispute_reason = models.CharField(max_length=200, blank=True, null=True)
    case_status = models.CharField(max_length=30, default="OPEN", db_index=True)
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("transaction_date", "rrn", "source_status")
        ordering = ["-transaction_date", "rrn"]

    def __str__(self):
        return f"RGCS {self.transaction_date} - {self.rrn} - {self.source_status}"


class IMPSDisputeCase(models.Model):
    transaction_date = models.DateField(db_index=True)
    transaction_serial_number = models.CharField(max_length=50, db_index=True)
    rrn = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    disputed_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    source_status = models.CharField(max_length=50, db_index=True)
    dispute_reason = models.CharField(max_length=200, blank=True, null=True)
    case_status = models.CharField(max_length=30, default="OPEN", db_index=True)
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("transaction_date", "transaction_serial_number", "source_status")
        ordering = ["-transaction_date", "transaction_serial_number"]

    def __str__(self):
        return f"IMPS {self.transaction_date} - {self.transaction_serial_number} - {self.source_status}"
