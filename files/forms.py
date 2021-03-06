from django import forms

class SpeakerDirectoryForm(forms.Form):
    speaker = forms.CharField()
    directory = forms.FileField(widget=forms.ClearableFileInput(attrs=
        {'multiple': True, 'webkitdirectory': True, 'directory': True, 
        'onchange':'speakerdirectoryform.submit();'}))