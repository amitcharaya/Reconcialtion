# gl_recon/models.py

from django.db import models
from decimal import Decimal

PRODUCT_CHOICES = (
    ("ATM", "ATM"),
    ("POS", "POS"),
    ("ECOM", "ECOM"),
    ("IMPS", "IMPS"),
)

GL_TYPE_CHOICES = (
    ("WITHDRAWAL", "Withdrawal"),
    ("FEE", "Fee"),
    ("GST", "GST"),
    ("NPCI", "NPCI Switching Fee"),
    ("NPCI_GST", "NPCI Switching Fee GST"),
    ("SETTLEMENT", "Settlement"),
)

class GLAccount(models.Model):
    name = models.CharField(max_length=100)
    gl_code = models.CharField(max_length=20, unique=True)
    product = models.CharField(max_length=10, choices=PRODUCT_CHOICES)
    gl_type = models.CharField(max_length=20, choices=GL_TYPE_CHOICES)

    def __str__(self):
        return f"{self.product} - {self.gl_type} ({self.gl_code})"

from decimal import Decimal
from django.db import models

class GLDailyBalance(models.Model):
    gl_account = models.ForeignKey(GLAccount, on_delete=models.CASCADE)
    balance_date = models.DateField()

    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    debit_during_the_day = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    credit_during_the_day = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    closing_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = ("gl_account", "balance_date")

    def save(self, *args, **kwargs):
        self.closing_balance = (
            self.opening_balance
            + self.credit_during_the_day
            - self.debit_during_the_day
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.gl_account} - {self.balance_date}"


class GLPending(models.Model):
    date = models.DateField()
    product = models.CharField(max_length=10, choices=PRODUCT_CHOICES)

    approved_fee = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    approved_fee_gst = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    switching_fee = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    switching_fee_gst = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    posted = models.BooleanField(default=False)  # becomes True after month posting

    class Meta:
        unique_together = ("date", "product")


class GLMapping(models.Model):
    product = models.CharField(max_length=10, choices=PRODUCT_CHOICES)
    gl_type = models.CharField(max_length=20, choices=GL_TYPE_CHOICES)

    # Source identifiers
    source = models.CharField(max_length=20)
    # Example: CBS, NTSL, SWITCH

    key = models.CharField(max_length=100)
    # Example:
    # "ACQ_WDL"
    # "ISS_WDL"
    # "ACQ_FEE"
    # "GST"

    def __str__(self):
        return f"{self.product} - {self.gl_type} - {self.key}"