"""
Form definitions for the reconciliation application. Forms validate user input before files or filters are processed.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django import forms


class ATMReconciliationForm(forms.Form):
    transaction_date = forms.DateField(
        label="Transaction Date",
        widget=forms.DateInput(attrs={"type": "date"})
    )
class ReconciliationDateForm(forms.Form):
    transaction_date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date"}
        )
    )


class ReconciliationReportForm(forms.Form):
    transaction_date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date"}
        )
    )

    report_type = forms.ChoiceField(
        choices=[
            ("ALL", "Full Report"),
            ("MATCHED_ALL", "Matched Only"),
            ("CBS_ONLY", "CBS Only"),
            ("SWITCH_ONLY", "Switch Only"),
            ("NDPG_ONLY", "NDPG Only"),
            ("CBS_NDPG_ONLY", "CBS And NDPG Only"),
            ("CBS_SWITCH_ONLY", "CBS And Switch Only"),
            ("NDPG_SWITCH_ONLY", "NDPG And Switch Only"),

        ]
    )