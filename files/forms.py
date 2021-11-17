from django import forms

class SpeakerDirectoryForm(forms.Form):
    speaker = forms.CharField(required=True)
    directory = forms.FileField(widget=forms.ClearableFileInput(attrs=
        {'multiple': True, 
        'onchange':'speakerdirectoryform.submit();'}))