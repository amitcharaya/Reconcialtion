"""
Data model definitions for the cbs application. These classes define tables, fields, relationships, and core database structure.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django.db import models

# Create your models here.

class UploadBatch(models.Model):
    """
        Stores CBS upload batch information.

        One upload operation may contain:
            Acquirer File
            Issuer File
            Onus File

        This model provides complete audit
        information for every upload.
        """

    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    batch_date = models.DateField()

    acquirer_filename = models.CharField(max_length=255)
    issuer_filename = models.CharField(max_length=255)
    onus_filename = models.CharField(max_length=255)

    total_records = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)

    upload_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    remarks = models.TextField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch_date} - {self.upload_status}"


class CBSATMTransaction(models.Model):
    FILE_TYPE_CHOICES = [
        ('A', 'Acquirer'),
        ('I', 'Issuer'),
        ('O', 'On-Us'),
    ]
    DR_CR_CHOICES = [
        ('D', 'Debit'),
        ('C', 'Credit'),
    ]
    # Core Identity
    stan_no = models.CharField(max_length=6)
    card_no = models.CharField(max_length=19)
    rrn_no= models.CharField(max_length=12)
    account_type = models.CharField(max_length=2)

    # Account / GL Layer
    customer_account_no = models.CharField(max_length=18,blank=True,null=True)
    acquirer_gl = models.CharField(max_length=18,blank=True,null=True)
    acquirer_gl_name = models.CharField(max_length=50,blank=True,null=True)
    customer_name = models.CharField(max_length=100,blank=True,null=True)
    # Branch Layer
    branch_id = models.CharField(max_length=4)
    branch_name = models.CharField(max_length=50)
    # Classification
    file_type = models.CharField(max_length=1,choices=FILE_TYPE_CHOICES)
    dr_cr_flag = models.CharField(max_length=1,choices=DR_CR_CHOICES )
    # Financial Layer
    txn_amount = models.DecimalField(max_digits=15,decimal_places=2 )
    # Date and Time
    txn_date = models.DateField()
    txn_time = models.CharField(max_length=6)
    settlement_date = models.DateField()
    settlement_time = models.CharField( max_length=6,blank=True,null=True)
    # ATM Layer
    atm_id = models.CharField(max_length=8)
    acquirer_bank = models.CharField(max_length=10,blank=True,null=True)
    unknown_data = models.CharField(max_length=20,blank=True, null=True)
    atm_location = models.CharField(max_length=100)
    # Status
    status = models.CharField(max_length=2)
    # Audit Layer
    raw_record = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.stan_no} - {self.file_type} - {self.txn_amount}"









class CBSIMPSUploadBatch(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    batch_date = models.DateField()
    acquirer_filename = models.CharField(max_length=255)
    issuer_filename = models.CharField(max_length=255)
    onus_filename = models.CharField(max_length=255)

    total_records = models.PositiveIntegerField(default=0)
    total_errors = models.PositiveIntegerField(default=0)

    upload_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="FAILED"
    )

    remarks = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("batch_date", "acquirer_filename")

    def __str__(self):
        return f"{self.batch_date} -  {self.upload_status}"


class CBSIMPSTransaction(models.Model):
    batch = models.ForeignKey(
        CBSIMPSUploadBatch,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    transaction_serial_number = models.CharField(max_length=12, db_index=True)
    account_type = models.CharField(max_length=2)
    account_number = models.CharField(max_length=18)
    account_holder_name = models.CharField(max_length=26,null=True,blank=True)
    branch_code = models.CharField(max_length=4)
    branch_name = models.CharField(max_length=25)

    nbin = models.CharField(max_length=4)
    mobile_number = models.CharField(max_length=10, blank=True, null=True)
    ifsc = models.CharField(max_length=11, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)

    transaction_type = models.CharField(max_length=1)  # I/A/O
    dr_cr_flag = models.CharField(max_length=1)        # D/C

    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)

    transaction_code = models.CharField(max_length=2)
    rem_bene_nbin = models.CharField(max_length=4)
    rem_bene_mobile_number = models.CharField(max_length=10, blank=True, null=True)
    rem_bene_ifsc = models.CharField(max_length=11, blank=True, null=True)
    rem_bene_account_number = models.CharField(max_length=18, blank=True, null=True)
    rem_bene_aadhaar_number = models.CharField(max_length=12, blank=True, null=True)

    transaction_date = models.DateField(db_index=True)
    transaction_time = models.TimeField(db_index=True)

    value_date = models.DateField()
    value_time = models.TimeField()

    original_channel = models.CharField(max_length=3)
    atm_id = models.CharField(max_length=8, blank=True, null=True)
    remark = models.CharField(max_length=15, blank=True, null=True)
    response_code = models.CharField(max_length=2)

    raw_data = models.TextField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "transaction_serial_number",
            "transaction_date",
            "transaction_time",
            "transaction_amount",
            "dr_cr_flag",
        )

    def __str__(self):
        return f"{self.transaction_serial_number} - {self.transaction_amount}"


"""RGCS Models"""



class RGCSUploadBatch(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("PARTIAL", "Partial Success"),
    ]

    batch_date = models.DateField()

    source_filename = models.CharField(max_length=255)

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
        return f"RGCS Batch - {self.batch_date} - {self.source_filename}"


class RGCSCBSTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ("44", "Cash at POS"),
        ("45", "Purchase"),
        ("46", "Purchase with Cash Back"),
        ("49", "E-Commerce"),
    ]

    TRANSACTION_FLAG_CHOICES = [
        ("I", "Issuer"),
        ("A", "Acquirer"),
    ]

    DR_CR_CHOICES = [
        ("D", "Debit"),
        ("C", "Credit"),
    ]

    batch = models.ForeignKey(
        RGCSUploadBatch,
        on_delete=models.CASCADE,
        related_name="cbs_transactions"
    )

    source_filename = models.CharField(max_length=255)

    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES)

    stan_no = models.CharField(max_length=6)
    card_no = models.CharField(max_length=19)
    rrn = models.CharField(max_length=12)

    account_type = models.CharField(max_length=2)
    account_number = models.CharField(max_length=18)
    account_holder_name = models.CharField(max_length=26)

    branch_code = models.CharField(max_length=4)
    branch_name = models.CharField(max_length=25)

    transaction_flag = models.CharField(max_length=1, choices=TRANSACTION_FLAG_CHOICES)
    dr_cr_flag = models.CharField(max_length=1, choices=DR_CR_CHOICES)

    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)

    transaction_date = models.DateField()
    transaction_time = models.TimeField()

    value_date = models.DateField()
    value_time = models.TimeField()

    acquirer_institution_code = models.CharField(max_length=6)

    terminal_id = models.CharField(max_length=8)
    terminal_location = models.CharField(max_length=40)

    response_code = models.CharField(max_length=2)

    raw_record = models.TextField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["stan_no"]),
            models.Index(fields=["rrn"]),
            models.Index(fields=["card_no"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["transaction_flag"]),
        ]

    def __str__(self):
        return f"{self.transaction_flag} | {self.stan_no} | {self.rrn}"