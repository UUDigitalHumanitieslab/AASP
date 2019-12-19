from django import forms

class FileFieldForm(forms.Form):
    speaker = forms.CharField(max_length=100)
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))