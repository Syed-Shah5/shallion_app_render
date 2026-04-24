from django import forms

class RespondToMatchForm(forms.Form):
    CHOICES = [
        ('accept', 'Accept'),
        ('reject', 'Reject'),
    ]
    response = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
