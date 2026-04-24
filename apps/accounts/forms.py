import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import User

# Client Registration Form
class ClientRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Create Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password','class': 'form-control'}),
        min_length=8
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password','class': 'form-control'})
    )
    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must accept the terms and conditions'}
    )
    gp_certificate = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png','class': 'file-input'}),
        help_text='Upload GP certificate (PDF, JPG, PNG, max 5MB)'
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Enter your full name','class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email','class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number','class': 'form-control'}),
        }

    # Validation methods
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        words = full_name.strip().split()
        if len(words) < 2:
            raise forms.ValidationError("Please enter at least first and last name.")
        for word in words:
            if not word.replace('-', '').replace("'", "").isalpha():
                raise forms.ValidationError("Full name can only contain letters, hyphens, or apostrophes.")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        normalized = re.sub(r'[\s\-]', '', phone)
        if not re.match(r'^(0\d{10}|\+44\d{10})$', normalized):
            raise forms.ValidationError("Enter a valid UK phone number.")
        return normalized

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not password:
            raise forms.ValidationError("Password is required.")
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        checks = [
            re.search(r'[A-Z]', password),
            re.search(r'[a-z]', password),
            re.search(r'\d', password),
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        ]
        if sum(bool(c) for c in checks) < 3:
            raise forms.ValidationError("Password is too weak. Include at least 3 of: uppercase, lowercase, number, special character."
         )
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def clean_gp_certificate(self):
        gp_certificate = self.cleaned_data.get('gp_certificate')
        if gp_certificate:
            max_size = 5 * 1024 * 1024
            if gp_certificate.size > max_size:
                raise forms.ValidationError('File size must be less than 5MB.')
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
            if gp_certificate.content_type not in allowed_types:
                raise forms.ValidationError('Only PDF, JPG, and PNG files are allowed.')
        return gp_certificate

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'CLIENT'
        user.status = 'PENDING'
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

# Volunteer Registration Form
class VolunteerRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Create Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password','class': 'form-control'}),
        min_length=8
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password','class': 'form-control'})
    )
    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must accept the terms and conditions'}
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'pvg_number']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Enter your full name','class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email','class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number','class': 'form-control'}),
            'pvg_number': forms.TextInput(attrs={'placeholder': 'Enter your PVG number','class': 'form-control'}),
        }

    # Validation methods
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        words = full_name.strip().split()
        if len(words) < 2:
            raise forms.ValidationError("Please enter at least first and last name.")
        for word in words:
            if not word.replace('-', '').replace("'", "").isalpha():
                raise forms.ValidationError("Full name can only contain letters, hyphens, or apostrophes.")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        normalized = re.sub(r'[\s\-]', '', phone)
        if not re.match(r'^(0\d{10}|\+44\d{10})$', normalized):
            raise forms.ValidationError("Enter a valid UK phone number.")
        return normalized

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not password:
            raise forms.ValidationError("Password is required.")
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        checks = [
            re.search(r'[A-Z]', password),
            re.search(r'[a-z]', password),
            re.search(r'\d', password),
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        ]

        if sum(bool(c) for c in checks) < 3:
            raise forms.ValidationError("Password is too weak. Include at least 3 of: uppercase, lowercase, number, special character."
        )
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def clean_pvg_number(self):
        pvg_number = self.cleaned_data.get('pvg_number')
        if not pvg_number:
            raise forms.ValidationError("PVG number is required.")
        normalized = re.sub(r'[\s\-]', '', pvg_number)
        if not re.match(r'^\d{16}$', normalized):
            raise forms.ValidationError("PVG number must be exactly 16 digits.")
        if User.objects.filter(pvg_number=normalized).exists():
            raise forms.ValidationError("This PVG number is already registered.")
        return normalized

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'VOLUNTEER'
        user.status = 'PENDING'
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

# Client Login Form
class ClientLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email','class': 'form-control'}),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password','class': 'form-control'}),
        label='Password'
    )
    error_messages = {
        'invalid_login': "Please enter a correct email and password.",
        'inactive': "This account is inactive.",
    }

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email:
            email = email.lower() 
        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login'
                )
            if not user.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'],
                    code='inactive'
                )
            self.user_cache = user
        return self.cleaned_data

# Volunteer Login Form
class VolunteerLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email','class': 'form-control'}),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password','class': 'form-control'}),
        label='Password'
    )
    error_messages = {
        'invalid_login': "Please enter a correct email and password.",
        'inactive': "This account is inactive.",
    }

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email:
            email = email.lower()
        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login'
                )
            if not user.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'],
                    code='inactive'
                )
            self.user_cache = user
        return self.cleaned_data