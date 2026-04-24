from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (ClientRegistrationForm, VolunteerRegistrationForm,ClientLoginForm, VolunteerLoginForm)
from .tokens import generate_email_verification_token, verify_email_token, send_verification_email


# All Public Pages
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')
 
def how_it_works(request):
    return render(request, 'how_it_works.html')

def help_page(request):
    return render(request, 'help.html')

# Client Authentication
def client_login(request):
    if request.method == 'POST':
        form = ClientLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and user.role == 'CLIENT':
                if user.status == 'ACTIVE':
                    login(request, user)
                    messages.success(request, 'Logged in successfully!')
                    return redirect('client:dashboard')
                else:
                    messages.error(request, 'Your account is not active.')
            else:
                messages.error(request, 'Invalid credentials.')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = ClientLoginForm()
    return render(request, 'accounts/client_login.html', {'form': form})


def client_register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            if 'gp_certificate' in request.FILES:
                user.gp_certificate = request.FILES['gp_certificate']
                user.save()
            generate_email_verification_token(user)  # Generate signed token
            send_verification_email(user) # Send verification email
            messages.success(
                request,
                'Account created! Please check your email to verify your account.'
            )
            return redirect('accounts:client_register_confirmation')
    else:
        form = ClientRegistrationForm()
    return render(request, 'accounts/client_register.html', {'form': form})

def client_register_confirmation(request):
    return render(request, 'accounts/client_register_confirmation.html')

@login_required
def client_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('accounts:client_login')

# Volunteer Authentication
def volunteer_login(request):
    if request.method == 'POST':
        form = VolunteerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and user.role == 'VOLUNTEER':
                if user.status == 'ACTIVE':
                    login(request, user)
                    messages.success(request, 'Logged in successfully!')
                    return redirect('volunteer:dashboard')
                else:
                    messages.error(request, 'Your account is not active.')
            else:
                messages.error(request, 'Invalid credentials.')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = VolunteerLoginForm()
    return render(request, 'accounts/volunteer_login.html', {'form': form})


def volunteer_register(request):
    if request.method == 'POST':
        form = VolunteerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            generate_email_verification_token(user) # Generate signed token
            send_verification_email(user) # Send verification email
            messages.success(
                request,
                'Volunteer account created! Please verify your email.'
            )
            return redirect('accounts:volunteer_register_confirmation')
    else:
        form = VolunteerRegistrationForm()
    return render(request, 'accounts/volunteer_register.html', {'form': form})

def volunteer_register_confirmation(request):
    return render(request, 'accounts/volunteer_register_confirmation.html')

@login_required
def volunteer_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('accounts:volunteer_login')

# Email Verification
def verify_email(request, token):
    user = verify_email_token(token)
    if user:
        messages.success(request, 'Email verified successfully!')
        # Activate if other verification completed
        if user.role == 'CLIENT' and user.gp_certificate_verified:
            user.status = 'ACTIVE'
            user.save()
        elif user.role == 'VOLUNTEER' and user.pvg_verified:
            user.status = 'ACTIVE'
            user.save()
        return redirect('home')
    else:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('home')
    
    
