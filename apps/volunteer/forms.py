import re
from django import forms
from django.contrib.auth import get_user_model
from .models import VolunteerProfile, VolunteerPreferences
from django.core.exceptions import ValidationError
from datetime import date

User = get_user_model()

PHONE_REGEX = re.compile(r'^(\+44\s?|0)[1-9](\d\s?){8,9}\d$')
UK_POSTCODE_REGEX = re.compile(r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$', re.IGNORECASE)
NAME_REGEX = re.compile(r"^[A-Za-z][A-Za-z\s'\-]{0,49}$")

# Form for creating/updating volunteer profile
class VolunteerProfileForm(forms.ModelForm):
    
    class Meta:
        model = VolunteerProfile
        fields = [
            'forename', 'surname', 'gender', 'phone', 'profile_photo',
            'address_line1', 'address_line2', 'city', 'postcode',
            'date_of_birth',
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relationship', 'bio', 'skills_description'
        ]
        widgets = {
            'forename': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postcode': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'skills_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def clean_forename(self):
        value = self.cleaned_data['forename'].strip()
        if len(value) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        if not NAME_REGEX.match(value):
            raise ValidationError("First name may only contain letters, spaces, hyphens, and apostrophes.")
        return value.title()

    def clean_surname(self):
        value = self.cleaned_data['surname'].strip()
        if len(value) < 2:
            raise ValidationError("Last name must be at least 2 characters.")
        if not NAME_REGEX.match(value):
            raise ValidationError("Last name may only contain letters, spaces, hyphens, and apostrophes.")
        return value.title()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError("Phone number is required.")
        if not PHONE_REGEX.match(phone):
            raise ValidationError("Enter a valid phone number (e.g. +447911123456). 9–15 digits.")
        return phone

    def clean_city(self):
        city = self.cleaned_data['city'].strip()
        if len(city) < 2:
            raise ValidationError("City name must be at least 2 characters.")
        if not re.match(r"^[A-Za-z][A-Za-z\s'\-]{0,99}$", city):
            raise ValidationError("City name may only contain letters, spaces, and hyphens.")
        return city.title()

    def clean_postcode(self):
        postcode = self.cleaned_data['postcode'].strip().upper()
        if not UK_POSTCODE_REGEX.match(postcode):
            raise ValidationError("Enter a valid UK postcode (e.g. SW1A 1AA).")
        return postcode

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        if dob > today:
            raise ValidationError("Date of birth cannot be in the future.")
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise ValidationError("Volunteer must be at least 18 years old.")
        if age > 120:
            raise ValidationError("Please enter a valid date of birth.")
        return dob

    def clean_emergency_contact_name(self):
        value = self.cleaned_data['emergency_contact_name'].strip()
        if len(value) < 2:
            raise ValidationError("Emergency contact name must be at least 2 characters.")
        if not NAME_REGEX.match(value):
            raise ValidationError("Emergency contact name may only contain letters, spaces, hyphens, and apostrophes.")
        return value.title()

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data['emergency_contact_phone'].strip()
        if not PHONE_REGEX.match(phone):
            raise ValidationError("Enter a valid phone number (e.g. +447911123456). 9–15 digits.")
        return phone

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo and hasattr(photo, 'content_type'):
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("Profile photo must be less than 5MB.")
            if photo.content_type not in ('image/jpeg', 'image/png', 'image/gif'):
                raise ValidationError("Please upload a JPEG, PNG, or GIF image.")
        return photo


# Form for creating/updating volunteer preferences
class VolunteerPreferencesForm(forms.ModelForm):
        
    preferred_languages = forms.MultipleChoiceField(
        choices=VolunteerPreferences.LANGUAGES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    preferred_days = forms.MultipleChoiceField(
        choices=VolunteerPreferences.DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    preferred_times = forms.MultipleChoiceField(
        choices=VolunteerPreferences.TIME_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    preferred_tasks = forms.MultipleChoiceField(
        choices=VolunteerPreferences.TASK_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    class Meta:
        model = VolunteerPreferences
        fields = [
            'preferred_gender', 'preferred_languages', 'preferred_days',
            'preferred_times', 'preferred_tasks','can_work_with_pets',
            'has_transportation', 'availability_notes'
        ]
        widgets = {
            'preferred_gender': forms.Select(attrs={'class': 'form-select'}),
            'availability_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Any specific availability notes...'}),
            'can_work_with_pets': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_transportation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    # Field-specific validations
    def clean_preferred_languages(self):
        languages = self.cleaned_data.get('preferred_languages')
        if not languages:
            raise ValidationError("Please select at least one preferred language.")
        return languages

    def clean_preferred_days(self):
        days = self.cleaned_data.get('preferred_days')
        if not days:
            raise ValidationError("Please select at least one preferred day.")
        return days

    def clean_preferred_times(self):
        times = self.cleaned_data.get('preferred_times')
        if not times:
            raise ValidationError("Please select at least one preferred time slot.")
        return times

    def clean_preferred_tasks(self):
        tasks = self.cleaned_data.get('preferred_tasks')
        if not tasks:
            raise ValidationError("Please select at least one task you're willing to help with.")
        return tasks
