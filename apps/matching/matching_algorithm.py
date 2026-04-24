from apps.client.models import ClientProfile, ClientPreferences
from apps.volunteer.models import VolunteerProfile, VolunteerPreferences
from .models import Match

# Extract area from postcode. E.g. 'SW1A 2AA' → 'SW1A'
def get_postcode_area(postcode):
    if not postcode:
        return ''
    # Return the outcode (first part before space)
    return postcode.upper().split()[0]

# Postcode scoring: same area = 10, otherwise = 5
def postcode_match_score(client_postcode, volunteer_postcode):
    if not client_postcode or not volunteer_postcode:
        return 0
    if get_postcode_area(client_postcode) == get_postcode_area(volunteer_postcode):
        return 10
    return 5

# Score 0-90 based on overlapping preferences
# Uses weighted scoring with partial matches for better granularity
def preference_match_score(client_prefs, volunteer_prefs):
    if not client_prefs or not volunteer_prefs:
        return 0, {}

    score = 0
    match_details = {}
    
    # Check language overlap - weighted by number of matching languages
    c_langs = set(client_prefs.preferred_languages or [])
    v_langs = set(volunteer_prefs.preferred_languages or [])
    lang_overlap = len(c_langs & v_langs)
    if lang_overlap > 0:
        lang_score = min(10, lang_overlap * 5)  # Max 10 points (2+ languages gives full points)
        score += lang_score
        match_details['languages'] = lang_score

    # Check day overlap - partial credit for multiple days
    c_days = set(client_prefs.preferred_days or [])
    v_days = set(volunteer_prefs.preferred_days or [])
    day_overlap = len(c_days & v_days)
    if day_overlap > 0:
        day_score = min(25, day_overlap * 8.33)  # Max 25 points (3+ days gives full points)
        score += day_score
        match_details['days'] = round(day_score, 1)

    # Check time slot - client and volunteer each select one time slot
    # Give maximum points (20) if they match, otherwise 0
    c_time = client_prefs.preferred_times[0] if client_prefs.preferred_times and len(client_prefs.preferred_times) > 0 else None
    v_time = volunteer_prefs.preferred_times[0] if volunteer_prefs.preferred_times and len(volunteer_prefs.preferred_times) > 0 else None
    if c_time and v_time and c_time == v_time:
        time_score = 20
        score += time_score
        match_details['times'] = time_score

    # Check task overlap - highest weight, considers task category alignment
    c_tasks = set(client_prefs.preferred_tasks or [])
    v_tasks = set(volunteer_prefs.preferred_tasks or [])
    task_overlap = len(c_tasks & v_tasks)
    if task_overlap > 0:
        task_score = min(25, task_overlap * 8.33)  # Max 25 points (3+ tasks gives full points)
        score += task_score
        match_details['tasks'] = task_score

    # Check gender preference - with flexible matching options
    pref_gender = getattr(client_prefs, 'preferred_gender', None)
    vol_gender = volunteer_prefs.volunteer.gender if hasattr(volunteer_prefs, 'volunteer') else None
    
    if not pref_gender or pref_gender == 'any' or pref_gender == '':
        gender_score = 10  # No preference = full points
    elif vol_gender and pref_gender == vol_gender:
        gender_score = 10
    elif vol_gender and pref_gender != vol_gender:
        gender_score = 0
    else:
        gender_score = 2.5  # Partial if gender info missing
    score += gender_score
    match_details['gender'] = gender_score

    return round(score, 1), match_details

# Return total match score (0-100), detailed notes and breakdown
def calculate_score(client, volunteer):
    client_prefs = getattr(client, 'preferences', None)
    volunteer_prefs = getattr(volunteer, 'preferences', None)
    
    # Calculate postcode score
    postcode_score = postcode_match_score(client.postcode, volunteer.postcode)
    
    # Calculate preference score with details
    if client_prefs and volunteer_prefs:
        pref_score, pref_details = preference_match_score(client_prefs, volunteer_prefs)
    else:
        pref_score = 0
        pref_details = {}
    
    # Calculate total
    total = round(min(postcode_score + pref_score, 100), 1)
    
    # Generate detailed notes
    client_area = get_postcode_area(client.postcode) if client.postcode else 'Unknown'
    volunteer_area = get_postcode_area(volunteer.postcode) if volunteer.postcode else 'Unknown'
    
    notes_parts = [
        f"Location: {postcode_score}/10 ({client_area} vs {volunteer_area})",
        f"Preferences: {pref_score:.1f}/90"
    ]
    
    notes = "\n".join(notes_parts)
    
    return total, notes, {
        'total': total,
        'postcode_score': postcode_score,
        'preference_score': pref_score,
        'preference_breakdown': pref_details
    }

# Create Match records for compatible volunteers. Updates existing PENDING matches
def generate_matches_for_client(client_profile, min_score=50):
    existing_ids = set(
        Match.objects.filter(client=client_profile)
        .exclude(status__in=['REJECTED', 'SUGGESTED', 'ACCEPTED', 'ACTIVE', 'COMPLETED'])
        .values_list('volunteer_id', flat=True)
    )
    
    for volunteer in VolunteerProfile.objects.filter(profile_completed=True):
        score, notes, _ = calculate_score(client_profile, volunteer)
        
        if score >= min_score:
            match, created = Match.objects.get_or_create(
                client=client_profile,
                volunteer=volunteer,
                defaults={
                    'status': 'PENDING',
                    'compatibility_score': score,
                    'matching_notes': notes,
                },
            )
            # Update existing PENDING matches with new scores (in case profiles were updated)
            if not created and match.status == 'PENDING':
                match.compatibility_score = score
                match.matching_notes = notes
                match.save()