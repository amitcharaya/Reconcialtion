from django import forms
from .models import GLAccount, GLOpeningBalance


class GLAccountForm(forms.ModelForm):
    class Meta:
        model = GLAccount
        fields = ["gl_code", "name", "product", "gl_type"]

class GLOpeningBalanceForm(forms.ModelForm):
    class Meta:
        model = GLOpeningBalance
        fields = ["opening_date", "opening_balance"]