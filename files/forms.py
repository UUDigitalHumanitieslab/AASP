from django import forms

class SpeakerDirectoryForm(forms.Form):
    speaker = forms.CharField(required=True)
    files = forms.FileField(widget=forms.ClearableFileInput(attrs=
        {'multiple': True}))