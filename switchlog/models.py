"""
Data model definitions for the switchlog application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models


class SwitchLogUploadBatch(models.Model):
    upload_date = models.DateField()
    filename = models.CharField(max_length=255)
    total_records = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.upload_date} - {self.filename}"

class SwitchATMTransaction(models.Model):
    batch = models.ForeignKey(
        SwitchLogUploadBatch,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sn = models.CharField(max_length=20, blank=True, null=True)
    transaction_datetime = models.DateTimeField()
    transaction_date = models.DateField()

    terminal_id = models.CharField(max_length=20, blank=True, null=True)
    terminal_type = models.CharField(max_length=30, blank=True, null=True)
    switch = models.CharField(max_length=30, blank=True, null=True)

    stan_no = models.CharField(max_length=20, blank=True, null=True)
    card_no = models.CharField(max_length=25, blank=True, null=True)

    account_type = models.CharField(max_length=30, blank=True, null=True)
    account_no = models.CharField(max_length=30, blank=True, null=True)
    beneficiary_account_no = models.CharField(max_length=30, blank=True, null=True)

    acquirer_bank = models.CharField(max_length=30, blank=True, null=True)
    rrn = models.CharField(max_length=30, blank=True, null=True)
    mcc = models.CharField(max_length=10, blank=True, null=True)

    transaction_type = models.CharField(max_length=50, blank=True, null=True)
    connected_transaction = models.CharField(max_length=50, blank=True, null=True)
    transaction_description = models.CharField(max_length=150, blank=True, null=True)

    amount_requested = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    interface_type = models.CharField(max_length=30, blank=True, null=True)
    void_code = models.CharField(max_length=30, blank=True, null=True)
    atm_location = models.CharField(max_length=150, blank=True, null=True)
    embossed_name = models.CharField(max_length=100, blank=True, null=True)

    transaction_status = models.CharField(max_length=50, blank=True, null=True)
    error = models.CharField(max_length=100, blank=True, null=True)

    raw_data = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_date} - {self.rrn or self.stan_no} - {self.transaction_amount}"


"imps model"




class SwitchIMPSUploadBatch(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    batch_date = models.DateField()
    filename = models.CharField(max_length=255)
    total_records = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)
    upload_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUCCESS"
    )
    remarks = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Switch IMPS Batch - {self.batch_date} - {self.filename}"


class SwitchIMPSTransaction(models.Model):
    batch = models.ForeignKey(
        SwitchIMPSUploadBatch,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    transaction_datetime = models.DateTimeField()
    transaction_id = models.CharField(max_length=100)
    transaction_category = models.CharField(max_length=100, blank=True, null=True)
    transaction_type = models.CharField(max_length=100, blank=True, null=True)
    transaction_particulars = models.TextField(blank=True, null=True)

    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    status = models.CharField(max_length=100, blank=True, null=True)
    rrn = models.CharField(max_length=50, blank=True, null=True)

    rem_mmid = models.CharField(max_length=50, blank=True, null=True)
    rem_account = models.CharField(max_length=50, blank=True, null=True)
    remitter_name = models.CharField(max_length=150, blank=True, null=True)
    rem_mobile = models.CharField(max_length=20, blank=True, null=True)

    bene_mas = models.CharField(max_length=50, blank=True, null=True)
    bene_nbin = models.CharField(max_length=50, blank=True, null=True)
    bene_mobile = models.CharField(max_length=20, blank=True, null=True)
    bene_account = models.CharField(max_length=50, blank=True, null=True)
    beneficiary_name = models.CharField(max_length=150, blank=True, null=True)
    beneficiary_ifsc = models.CharField(max_length=20, blank=True, null=True)

    product_indicator = models.CharField(max_length=100, blank=True, null=True)
    original_channel = models.CharField(max_length=100, blank=True, null=True)

    cbs_status = models.CharField(max_length=100, blank=True, null=True)
    cbs_rc = models.CharField(max_length=50, blank=True, null=True)
    cbs_reversal_status = models.CharField(max_length=100, blank=True, null=True)
    cbs_reversal_rc = models.CharField(max_length=50, blank=True, null=True)

    nfs_status = models.CharField(max_length=100, blank=True, null=True)
    nfs_verification_status = models.CharField(max_length=100, blank=True, null=True)
    nfs_verification_rc = models.CharField(max_length=50, blank=True, null=True)

    imps_rc = models.CharField(max_length=50, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    raw_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("transaction_id", "rrn", "transaction_amount", "transaction_datetime")

    def __str__(self):
        return f"{self.transaction_id} - {self.rrn} - {self.transaction_amount}"

"""RGCS Section"""



class RGCSSwitchUploadBatch(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    batch_date = models.DateField()
    source_filename = models.CharField(max_length=255, unique=True)

    total_records = models.PositiveIntegerField(default=0)
    total_errors = models.PositiveIntegerField(default=0)

    upload_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUCCESS"
    )

    remarks = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RGCS Switch - {self.batch_date} - {self.source_filename}"


class RGCSSwitchTransaction(models.Model):
    batch = models.ForeignKey(
        RGCSSwitchUploadBatch,
        on_delete=models.CASCADE,
        related_name="rgcs_switch_transactions"
    )

    source_filename = models.CharField(max_length=255)

    serial_no = models.PositiveIntegerField(blank=True, null=True)
    tranx_datetime = models.DateTimeField()
    tranx_date = models.DateField()
    tranx_time = models.TimeField()

    terminal_id = models.CharField(max_length=20, blank=True, null=True)
    terminal_type = models.CharField(max_length=20, blank=True, null=True)
    switch = models.CharField(max_length=50, blank=True, null=True)

    stan_no = models.CharField(max_length=20)
    card_no = models.CharField(max_length=30, blank=True, null=True)

    account_type = models.CharField(max_length=30, blank=True, null=True)
    account_no = models.CharField(max_length=30, blank=True, null=True)

    acq_bank = models.CharField(max_length=20, blank=True, null=True)
    rrn = models.CharField(max_length=20)

    mcc = models.CharField(max_length=10, blank=True, null=True)
    txn_type = models.CharField(max_length=50, blank=True, null=True)
    con_txn = models.CharField(max_length=10, blank=True, null=True)

    amount_req = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_approved = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    interface_type = models.CharField(max_length=20, blank=True, null=True)
    void_code = models.CharField(max_length=10, blank=True, null=True)

    atm_location = models.CharField(max_length=255, blank=True, null=True)
    embossed_name = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=50, blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    raw_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tranx_date"]),
            models.Index(fields=["stan_no"]),
            models.Index(fields=["rrn"]),
            models.Index(fields=["terminal_type"]),
            models.Index(fields=["interface_type"]),
        ]

    def __str__(self):
        return f"{self.tranx_date} - {self.rrn} - {self.amount_approved}"