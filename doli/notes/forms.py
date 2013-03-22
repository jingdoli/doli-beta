from django import forms
from models import Notes

class CreateNoteForm(forms.Form):
    title = forms.CharField(max_length=100)
    content = forms.CharField(widget=forms.widgets.Textarea() )
