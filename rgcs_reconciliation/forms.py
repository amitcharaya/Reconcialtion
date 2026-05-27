"""
Form definitions for the rgcs_reconciliation application. Forms validate user input before files or filters are processed.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django import forms


class RGCSReconciliationForm(forms.Form):
    transaction_date = forms.DateField(
        label="Transaction Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )