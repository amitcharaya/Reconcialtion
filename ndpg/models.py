"""
Data model definitions for the ndpg application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models

class NDPGUploadBatch(models.Model):
    upload_date = models.DateField()
    total_records = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    cycle_1_acquirer_filename = models.CharField(max_length=255)
    cycle_1_issuer_filename = models.CharField(max_length=255)
    cycle_2_acquirer_filename = models.CharField(max_length=255)
    cycle_2_issuer_filename = models.CharField(max_length=255)
    cycle_3_acquirer_filename = models.CharField(max_length=255)
    cycle_3_issuer_filename = models.CharField(max_length=255)
    cycle_4_acquirer_filename = models.CharField(max_length=255)
    cycle_4_issuer_filename = models.CharField(max_length=255)

    def __str__(self):
        return f"NDPG Upload - {self.upload_date}"
# Create your models here.
class NDPGATMTransaction(models.Model):

    FILE_TYPE_CHOICES = [
        ("ACQUIRER", "Acquirer"),
        ("ISSUER", "Issuer"),
    ]

    CYCLE_CHOICES = [
        ("1", "Cycle 1"),
        ("2", "Cycle 2"),
        ("3", "Cycle 3"),
        ("4", "Cycle 4"),
    ]
    batch = models.ForeignKey(
        NDPGUploadBatch,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    cycle_no = models.CharField(max_length=1, choices=CYCLE_CHOICES)

    participant_id = models.CharField(max_length=3)
    transaction_type = models.CharField(max_length=2)
    from_account_type = models.CharField(max_length=2)
    to_account_type = models.CharField(max_length=2)

    transaction_serial_number = models.CharField(max_length=12)
    response_code = models.CharField(max_length=2)
    pan_number = models.CharField(max_length=16)
    member_number = models.CharField(max_length=6)
    approval_number = models.CharField(max_length=6)
    stan_no = models.CharField(max_length=6)

    transaction_date = models.DateField()
    transaction_time = models.CharField(max_length=6)

    merchant_category_code = models.CharField(max_length=4)
    card_acceptor_settlement_date = models.CharField(max_length=6)
    card_acceptor_id = models.CharField(max_length=15)
    card_acceptor_terminal_id = models.CharField(max_length=8)
    card_acceptor_terminal_location = models.CharField(max_length=36)

    acquirer_id = models.CharField(max_length=15)

    acquirer_settlement_date = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    network_id = models.CharField(
        max_length=3,
        blank=True,
        null=True
    )

    account_1_number = models.CharField(
        max_length=16,
        blank=True,
        null=True
    )

    account_1_branch_id = models.CharField(
        max_length=13,
        blank=True,
        null=True
    )

    account_2_number = models.CharField(
        max_length=16,
        blank=True,
        null=True
    )

    account_2_branch_id = models.CharField(
        max_length=13,
        blank=True,
        null=True
    )

    transaction_currency_code = models.CharField(max_length=3)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)
    actual_transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_activity_fee = models.DecimalField(max_digits=15, decimal_places=2)

    raw_record = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} C{self.cycle_no} - {self.stan_no} - {self.transaction_amount}"

"IMPS Model"




class NDPGIMPSRawUploadBatch(models.Model):

    FILE_TYPE_CHOICES = [
        ("ACQUIRER", "Acquirer"),
        ("ISSUER", "Issuer"),
    ]

    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        db_index=True
    )

    file_date = models.DateField(db_index=True)
    cycle_no = models.PositiveIntegerField(db_index=True)

    raw_header = models.CharField(max_length=100)
    source_filename = models.CharField(max_length=255)

    eof_record_count = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    total_records = models.PositiveIntegerField(default=0)
    created_records = models.PositiveIntegerField(default=0)
    updated_records = models.PositiveIntegerField(default=0)
    skipped_records = models.PositiveIntegerField(default=0)

    upload_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="FAILED"
    )

    error_message = models.TextField(
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "file_type",
            "file_date",
            "cycle_no",
            "source_filename",
        )

    def __str__(self):
        return (
            f"{self.file_type} - {self.file_date} - "
            f"Cycle {self.cycle_no} - {self.upload_status}"
        )

class NDPGIMPSRawTransaction(models.Model):

    batch = models.ForeignKey(
        NDPGIMPSRawUploadBatch,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    FILE_TYPE_CHOICES = [
        ("ACQUIRER", "Acquirer"),
        ("ISSUER", "Issuer"),
    ]

    participant_id = models.CharField(max_length=20, blank=True, null=True)
    transaction_type = models.CharField(max_length=20, blank=True, null=True)

    from_account_type = models.CharField(max_length=10, blank=True, null=True)
    to_account_type = models.CharField(max_length=10, blank=True, null=True)

    transaction_serial_number = models.CharField(
        max_length=30,
        db_index=True
    )

    response_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        db_index=True
    )

    pan_number = models.CharField(max_length=30, blank=True, null=True)
    approval_no = models.CharField(max_length=30, blank=True, null=True)

    transaction_date = models.DateField(db_index=True)
    transaction_time = models.TimeField(blank=True, null=True)

    merchant_category_code = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    card_acceptor_settlement_date = models.DateField(
        blank=True,
        null=True,
        db_index=True
    )

    card_acceptor_id = models.CharField(max_length=50, blank=True, null=True)
    acquirer_id = models.CharField(max_length=30, blank=True, null=True)

    transaction_currency_code = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    actual_transaction_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    original_channel = models.CharField(max_length=20, blank=True, null=True)

    bene_ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    bene_account_no = models.CharField(max_length=40, blank=True, null=True)

    rem_ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    remitter_account_no = models.CharField(max_length=40, blank=True, null=True)

    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        db_index=True
    )

    file_date = models.DateField(db_index=True)
    cycle_no = models.PositiveIntegerField(db_index=True)

    source_filename = models.CharField(max_length=255)

    raw_header = models.CharField(max_length=100, blank=True, null=True)
    eof_record_count = models.PositiveIntegerField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "transaction_serial_number",
            "actual_transaction_amount",
            "file_type",
            "cycle_no",
            "file_date",
        )

    def __str__(self):
        return (
            f"{self.file_type} Cycle {self.cycle_no} - "
            f"{self.transaction_serial_number} - {self.actual_transaction_amount}"
        )

"RGCS Section"

from django.db import models


class RGCSUploadBatch(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    RECORD_NATURE_CHOICES = [
        ("ISSUER", "Issuer"),
        ("ACQUIRER", "Acquirer"),
    ]

    batch_date = models.DateField()
    record_nature = models.CharField(
        max_length=20,
        choices=RECORD_NATURE_CHOICES,
        default="ISSUER"
    )

    file_861 = models.CharField(max_length=255, blank=True, null=True)
    file_862 = models.CharField(max_length=255, blank=True, null=True)
    file_863 = models.CharField(max_length=255, blank=True, null=True)
    file_864 = models.CharField(max_length=255, blank=True, null=True)

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
        return f"RGCS {self.record_nature} - {self.batch_date}"


class RGCSRawTransaction(models.Model):
    RECORD_NATURE_CHOICES = [
        ("ISSUER", "Issuer"),
        ("ACQUIRER", "Acquirer"),
    ]

    batch = models.ForeignKey(
        RGCSUploadBatch,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    record_nature = models.CharField(
        max_length=20,
        choices=RECORD_NATURE_CHOICES,
        default="ISSUER"
    )

    source_filename = models.CharField(max_length=255)

    message_type = models.CharField(max_length=2)
    product_id = models.CharField(max_length=3)
    transaction_type = models.CharField(max_length=2)

    from_account_type = models.CharField(max_length=2, blank=True, null=True)
    to_account_type = models.CharField(max_length=2, blank=True, null=True)

    action_code = models.CharField(max_length=1)
    response_code = models.CharField(max_length=2)

    pan_number = models.CharField(max_length=19)
    approval_number = models.CharField(max_length=6, blank=True, null=True)
    rrn = models.CharField(max_length=12)
    stan_no = models.CharField(max_length=6, blank=True, null=True)

    transaction_date = models.DateField()
    transaction_time = models.TimeField()
    transaction_datetime = models.DateTimeField()

    merchant_category_code = models.CharField(max_length=4, blank=True, null=True)
    card_acceptor_id = models.CharField(max_length=15, blank=True, null=True)
    terminal_id = models.CharField(max_length=8, blank=True, null=True)
    terminal_location = models.CharField(max_length=40, blank=True, null=True)

    acquirer_id = models.CharField(max_length=11, blank=True, null=True)

    transaction_currency_code = models.CharField(max_length=3, blank=True, null=True)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    card_holder_billing_currency = models.CharField(max_length=3, blank=True, null=True)
    card_holder_billing_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    actual_txn_currency_code = models.CharField(max_length=3, blank=True, null=True)
    actual_txn_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    raw_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["record_nature", "transaction_date"]),
            models.Index(fields=["rrn"]),
            models.Index(fields=["stan_no"]),
            models.Index(fields=["source_filename"]),
        ]

    def __str__(self):
        return f"{self.record_nature} {self.rrn} {self.transaction_amount}"