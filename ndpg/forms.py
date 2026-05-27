"""
Form definitions for the ndpg application. Forms validate user input before files or filters are processed.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from django import forms


class NDPGUploadForm(forms.Form):

    upload_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Upload / Transaction Date"
    )

    cycle_1_acquirer = forms.FileField()
    cycle_1_issuer = forms.FileField()

    cycle_2_acquirer = forms.FileField()
    cycle_2_issuer = forms.FileField()

    cycle_3_acquirer = forms.FileField()
    cycle_3_issuer = forms.FileField()

    cycle_4_acquirer = forms.FileField()
    cycle_4_issuer = forms.FileField()

"IMPS Forms"


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [
                super(MultipleFileField, self).clean(item, initial)
                for item in data
            ]

        return super().clean(data, initial)


class NDPGIMPSRawUploadForm(forms.Form):

    upload_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Upload / Transaction Date"
    )

    file_type = forms.ChoiceField(
        choices=[
            ("ACQUIRER", "Acquirer"),
            ("ISSUER", "Issuer"),
        ]
    )

    raw_files = MultipleFileField()




class RGCSRawUploadForm(forms.Form):
    RECORD_NATURE_CHOICES = [
        ("ISSUER", "Issuer"),
        ("ACQUIRER", "Acquirer"),
    ]

    batch_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    record_nature = forms.ChoiceField(
        choices=RECORD_NATURE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    file_861 = forms.FileField(required=False)
    file_862 = forms.FileField(required=False)
    file_863 = forms.FileField(required=False)
    file_864 = forms.FileField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        files = [
            cleaned_data.get("file_861"),
            cleaned_data.get("file_862"),
            cleaned_data.get("file_863"),
            cleaned_data.get("file_864"),
        ]

        if not any(files):
            raise forms.ValidationError("Please upload at least one RGCS raw data file.")

        return cleaned_data