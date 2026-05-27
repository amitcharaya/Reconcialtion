"""
Form definitions for the cbs application. Forms validate user input before files or filters are processed.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django import forms

class CBSUploadForm(forms.Form):
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Transaction Date"
    )
    acquirer_file = forms.FileField(required=True)
    issuer_file = forms.FileField(required=True)
    onus_file = forms.FileField(required=True)


class CBSIMPSUploadForm(forms.Form):
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Transaction Date"
    )
    acquirer_file = forms.FileField()
    issuer_file = forms.FileField()
    onus_file = forms.FileField()

class RGCSCBSUploadForm(forms.Form):
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "required": "required",
        }),
        required=True,
        label="Transaction Date"
    )

    rgcs_file = forms.FileField(
        required=True,
        label="RGCS CBS File"
    )