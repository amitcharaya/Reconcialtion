"""
Form definitions for the switchlog application. Forms validate user input before files or filters are processed.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django import forms


class SwitchLogUploadForm(forms.Form):
    upload_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Upload / Transaction Date"
    )
    switch_file = forms.FileField()

class SwitchIMPSUploadForm(forms.Form):
    upload_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Upload / Transaction Date"
    )
    switch_imps_file = forms.FileField(
        label="Upload Switch IMPS Excel File"
    )


class RGCSSwitchUploadForm(forms.Form):
    batch_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    switch_file = forms.FileField(
        widget=forms.FileInput(attrs={"class": "form-control"})
    )