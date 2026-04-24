from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Match
from .forms import RespondToMatchForm


# View match details
@login_required
def match_detail(request, match_id):
    
    match = get_object_or_404(Match, id=match_id)

    # Check authorization
    if request.user.role == 'CLIENT':
        if match.client.user != request.user:
            messages.error(request, "Access denied.")
            return redirect('home')
    elif request.user.role == 'VOLUNTEER':
        if match.volunteer.user != request.user:
            messages.error(request, "Access denied.")
            return redirect('home')
        # Volunteer can't see detail if client hasn't sent request
        if match.status == 'PENDING':
            messages.error(request, "Access denied.")
            return redirect('home')

    role = request.user.role
    other_profile = match.volunteer if role == 'CLIENT' else match.client
    
    # Get preferences for the other profile
    try:
        other_preferences = other_profile.preferences
    except:
        other_preferences = None

    return render(request, 'matching/match_detail.html', {
        'match': match,
        'role': role,
        'other_profile': other_profile,
        'other_preferences': other_preferences,
    })

# Client sends request or volunteer responds
@login_required
def respond_to_match(request, match_id):
    
    match = get_object_or_404(Match, id=match_id)

    # Authorization
    if request.user.role == 'CLIENT':
        if match.client.user != request.user or match.status != 'PENDING':
            messages.error(request, "Cannot respond to this match.")
            return redirect('home')
        
        # Check if client already has a pending/active request (if required in future)
        '''existing_active = Match.objects.filter(
            client=match.client,
            status__in=['SUGGESTED', 'ACCEPTED', 'ACTIVE']
        ).exists()
        
        if existing_active:
            messages.error(request, "You already have a pending or active request. Please wait for a decision before sending another request.")
            return redirect('client:matched_volunteers')'''
    elif request.user.role == 'VOLUNTEER':
        if match.volunteer.user != request.user or match.status != 'SUGGESTED':
            messages.error(request, "Cannot respond to this match.")
            return redirect('home')
    else:
        messages.error(request, "Access denied.")
        return redirect('home')

    if request.method == 'POST':
        form = RespondToMatchForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['response'] == 'accept':
                if request.user.role == 'CLIENT':
                    match.send_request_to_volunteer()
                    messages.success(request, "Request sent to volunteer!")
                else:
                    match.accept_by_volunteer()
                    messages.success(request, "Match accepted!")
            else:
                match.reject()
                messages.info(request, "Match declined.")
            
            return redirect('matching:match_detail', match_id=match.id)
    else:
        form = RespondToMatchForm()

    return render(request, 'matching/respond_to_match.html', {
        'match': match,
        'form': form,
        'role': request.user.role,
    })
