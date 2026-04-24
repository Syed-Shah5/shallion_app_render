from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ClientProfile, ClientPreferences
from .forms import ClientProfileForm, ClientPreferencesForm
from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.http import JsonResponse
from apps.matching.models import Match
from apps.matching.matching_algorithm import generate_matches_for_client

User = get_user_model()

@login_required
def dashboard(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    try:
        profile = request.user.client_profile
    except ClientProfile.DoesNotExist:
        return redirect('client:create_profile')

    try:
        preferences = profile.preferences
    except ClientPreferences.DoesNotExist:
        preferences = None

    # Get matched volunteers for dashboard
    # matches = Match.objects.filter(client=profile).select_related('volunteer').order_by('-created_at')[:5]
    matches = Match.objects.filter(client=profile).exclude(status='REJECTED').select_related('volunteer').order_by('-created_at')[:5]
    context = {
        'profile': profile,
        'preferences': preferences,
        'page_title': 'Client Dashboard',
        'matched_volunteers': matches,
    }
    return render(request, 'client/dashboard.html', context)

@login_required
def create_profile(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    try:
        profile = request.user.client_profile
        return redirect('client:edit_profile')
    except ClientProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ClientProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile created. Set preferences next.")
            return redirect('client:create_preferences')
    else:
        form = ClientProfileForm()
    
    return render(request, 'client/profile_form.html', {'form': form, 'page_title': 'Create Profile'})


@login_required
def edit_profile(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    profile = get_object_or_404(ClientProfile, user=request.user)

    if request.method == 'POST':
        form = ClientProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('client:dashboard')
    else:
        form = ClientProfileForm(instance=profile)

    return render(request, 'client/profile_form.html', {'form': form, 'page_title': 'Edit Profile', 'profile': profile})

@login_required
def create_preferences(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    profile = get_object_or_404(ClientProfile, user=request.user)

    try:
        preferences = profile.preferences
        return redirect('client:edit_preferences')
    except ClientPreferences.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ClientPreferencesForm(request.POST)
        if form.is_valid():
            preferences = form.save(commit=False)
            preferences.client = profile
            preferences.save()
            profile.profile_completed = True
            profile.save()
            messages.success(request, "Preferences saved. Profile complete.")
            return redirect('client:dashboard')
    else:
        form = ClientPreferencesForm()

    return render(request, 'client/preferences_form.html', {'form': form, 'page_title': 'Set Preferences'})


@login_required
def edit_preferences(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    profile = get_object_or_404(ClientProfile, user=request.user)
    preferences = get_object_or_404(ClientPreferences, client=profile)

    if request.method == 'POST':
        form = ClientPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Preferences updated.")
            return redirect('client:dashboard')
    else:
        form = ClientPreferencesForm(instance=preferences)

    return render(request, 'client/preferences_form.html', {'form': form, 'page_title': 'Edit Preferences'})

@login_required
def view_profile(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    profile = get_object_or_404(ClientProfile, user=request.user)
    try:
        preferences = profile.preferences
    except ClientPreferences.DoesNotExist:
        preferences = None

    return render(request, 'client/view_profile.html', {'profile': profile, 'preferences': preferences})

@login_required
def matched_volunteers(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    profile = get_object_or_404(ClientProfile, user=request.user)
    
    # Generate new matches on-demand (if any new compatible volunteers available)
    # This runs every time the user views the page, finding new matches
    generate_matches_for_client(profile, min_score=50)
    
    # Get top 5 matches for this client from the matching app
    # Sorted by compatibility score (highest first)
    # matches = Match.objects.filter(client=profile).select_related('volunteer').order_by('-compatibility_score', '-created_at')[:5]
    matches = Match.objects.filter(client=profile).exclude(status='REJECTED').select_related('volunteer').order_by('-compatibility_score', '-created_at')[:5]
    return render(request, 'client/matched_volunteers.html', {
        'profile': profile,
        'matched_volunteers': matches,
    })

@login_required
def update_availability(request):
    if request.user.role != 'CLIENT':
        return JsonResponse({'error': 'Access denied'}, status=403)

    profile = get_object_or_404(ClientProfile, user=request.user)
    try:
        preferences = profile.preferences
        if request.method == 'POST':
            preferences.preferred_days = request.POST.getlist('preferred_days', preferences.preferred_days)
            preferences.preferred_times = request.POST.getlist('preferred_times', preferences.preferred_times)
            preferences.availability_notes = request.POST.get('availability_notes', preferences.availability_notes)
            preferences.save()
            return JsonResponse({'success': True})
    except ClientPreferences.DoesNotExist:
        return JsonResponse({'error': 'Preferences not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def delete_account(request):
    if request.user.role != 'CLIENT':
        messages.error(request, "Access denied.")
        return redirect('home')

    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Account deleted.")
        return redirect('home')

    return render(request, 'client/delete_account.html')