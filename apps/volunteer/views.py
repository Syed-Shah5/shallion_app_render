from django.contrib.auth import get_user_model
from .models import VolunteerProfile, VolunteerPreferences
from .forms import VolunteerProfileForm, VolunteerPreferencesForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import logout
from apps.matching.models import Match
from django.core.paginator import Paginator

User = get_user_model()

@login_required
def dashboard(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied. Volunteer access only.")
        return redirect('home')
    
    try:
        profile = request.user.volunteer_profile
    except VolunteerProfile.DoesNotExist:
        return redirect('volunteer:create_profile')
    
    try:
        preferences = profile.preferences
    except VolunteerPreferences.DoesNotExist:
        preferences = None
    
    # Fetch matched clients for dashboard
    # Only show SUGGESTED, ACCEPTED, ACTIVE, COMPLETED matches on dashboard
    matches = Match.objects.filter(
        volunteer=profile,
        status__in=['SUGGESTED', 'ACCEPTED', 'ACTIVE', 'COMPLETED']
    ).select_related('client').order_by('-created_at')[:5]
    matched_clients = matches
    
    context = {
        'profile': profile,
        'preferences': preferences,
        'matched_clients': matched_clients,
        'page_title': 'Volunteer Dashboard',
     
    }
    return render(request, 'volunteer/dashboard.html', context)
    
@login_required
def create_profile(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied. Volunteer access only.")
        return redirect('home')
    
    # Check if profile already exists
    try:
        profile = request.user.volunteer_profile
        return redirect('volunteer:edit_profile')
    except VolunteerProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = VolunteerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            messages.success(request, "Profile created. Set preferences next.")
            return redirect('volunteer:create_preferences')
    else:
        form = VolunteerProfileForm()
    
    return render(request, 'volunteer/profile_form.html', {'form': form, 'page_title': 'Create Profile'})

@login_required
def edit_profile(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied. Volunteer access only.")
        return redirect('home')
    
    profile = get_object_or_404(VolunteerProfile, user=request.user)
    
    if request.method == 'POST':
        form = VolunteerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('volunteer:dashboard')
    else:
        form = VolunteerProfileForm(instance=profile)
    
    return render(request, 'volunteer/profile_form.html', {'form': form, 'page_title': 'Edit Profile', 'profile': profile})

@login_required
def create_preferences(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied. Volunteer access only.")
        return redirect('home')
    
    profile = get_object_or_404(VolunteerProfile, user=request.user)
    
    # Check if preferences already exist
    try:
        preferences = profile.preferences
        return redirect('volunteer:edit_preferences')
    except VolunteerPreferences.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = VolunteerPreferencesForm(request.POST)
        if form.is_valid():
            preferences = form.save(commit=False)
            preferences.volunteer = profile
            preferences.save()
            profile.profile_completed = True
            profile.save()
            
            messages.success(request, "Preferences saved. Profile complete.")
            return redirect('volunteer:dashboard')
    else:
        form = VolunteerPreferencesForm()
    
    return render(request, 'volunteer/preferences_form.html', {'form': form, 'page_title': 'Set Preferences', 'profile': profile})

@login_required
def edit_preferences(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    profile = get_object_or_404(VolunteerProfile, user=request.user)
    preferences = get_object_or_404(VolunteerPreferences, volunteer=profile)
    
    if request.method == 'POST':
        form = VolunteerPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Preferences updated.")
            return redirect('volunteer:dashboard')
    else:
            form = VolunteerPreferencesForm(instance=preferences)
    
    return render(request, 'volunteer/preferences_form.html', {'form': form, 'page_title': 'Edit Preferences', 'profile': profile})

@login_required
def view_profile(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    profile = get_object_or_404(VolunteerProfile, user=request.user)
    
    try:
        preferences = profile.preferences
    except VolunteerPreferences.DoesNotExist:
        preferences = None
    
    return render(request, 'volunteer/view_profile.html', {'profile': profile, 'preferences': preferences, 'page_title': 'My Profile'})

@login_required
def matched_clients(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied. Volunteer access only.")
        return redirect('home')
    
    profile = get_object_or_404(VolunteerProfile, user=request.user)
    
    # Get matches for this volunteer from the matching app
    # Only show SUGGESTED, ACCEPTED, ACTIVE, COMPLETED matches on dashboard
    matches = Match.objects.filter(
        volunteer=profile,
        status__in=['SUGGESTED', 'ACCEPTED', 'ACTIVE', 'COMPLETED']
    ).select_related('client').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(matches, 9)  # Show 9 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': profile,
        'page_obj': page_obj,
        'matched_clients': page_obj.object_list,
        'page_title': 'Matched Clients'
    }
    return render(request, 'volunteer/matched_clients.html', context)

@login_required
def update_availability(request):
    if request.user.role != 'VOLUNTEER':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    profile = get_object_or_404(VolunteerProfile, user=request.user)
  
    try:
        preferences = profile.preferences
        if request.method == 'POST':
            preferences.preferred_days = request.POST.getlist('preferred_days', preferences.preferred_days)
            preferences.preferred_times = request.POST.getlist('preferred_times', preferences.preferred_times)
            preferences.availability_notes = request.POST.get('availability_notes', preferences.availability_notes)
            preferences.save()
            return JsonResponse({'success': True})
    except VolunteerPreferences.DoesNotExist:
            return JsonResponse({'error': 'Preferences not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def delete_account(request):
    if request.user.role != 'VOLUNTEER':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Account deleted.")
        return redirect('home')
    
    return render(request, 'volunteer/delete_account.html')
