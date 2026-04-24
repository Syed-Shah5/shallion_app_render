import pytest
from datetime import date
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError

from apps.client.models import ClientProfile, ClientPreferences
from apps.volunteer.models import VolunteerProfile, VolunteerPreferences
from apps.matching.models import Match
from apps.matching.forms import RespondToMatchForm
from apps.matching.matching_algorithm import (
    get_postcode_area,
    postcode_match_score,
    preference_match_score,
    calculate_score,
    generate_matches_for_client,
)

User = get_user_model()

# FIXTURES
@pytest.fixture
def client_user(db):
    user = User.objects.create_user(
        email='client@test.com',
        password='testpass123',
        role='CLIENT',
        full_name='John Client'
    )
    profile = ClientProfile.objects.create(
        user=user,
        forename='John',
        surname='Client',
        gender='M',
        phone='+44712345678',
        address_line1='123 Main St',
        city='London',
        postcode='SW1A 2AA',
        date_of_birth=date(1990, 1, 1),
        emergency_contact_name='Jane Client',
        emergency_contact_phone='+44712345679',
        emergency_contact_relationship='Wife',
        profile_completed=True
    )
    return user, profile

@pytest.fixture
def volunteer_user(db):
    user = User.objects.create_user(
        email='volunteer@test.com',
        password='testpass123',
        role='VOLUNTEER',
        full_name='Alice Volunteer'
    )
    profile = VolunteerProfile.objects.create(
        user=user,
        forename='Alice',
        surname='Volunteer',
        gender='F',
        phone='+44712345680',
        address_line1='456 High St',
        city='London',
        postcode='SW1A 1AA',
        date_of_birth=date(1985, 5, 15),
        emergency_contact_name='Bob Volunteer',
        emergency_contact_phone='+44712345681',
        emergency_contact_relationship='Brother',
        profile_completed=True
    )
    return user, profile

@pytest.fixture
def match(db, client_user, volunteer_user):
    _, client_profile = client_user
    _, volunteer_profile = volunteer_user
    return Match.objects.create(
        client=client_profile,
        volunteer=volunteer_profile,
        status='PENDING',
        compatibility_score=75
    )

# MODEL TESTS
@pytest.mark.django_db
def test_match_creation(match):
    assert match.status == 'PENDING'
    assert match.compatibility_score == 75
    assert not match.client_accepted
    assert not match.volunteer_accepted

@pytest.mark.django_db
def test_match_unique_constraint(client_user, volunteer_user):
    _, client_profile = client_user
    _, volunteer_profile = volunteer_user

    Match.objects.create(client=client_profile, volunteer=volunteer_profile)

    with pytest.raises(IntegrityError):
        Match.objects.create(client=client_profile, volunteer=volunteer_profile)

@pytest.mark.django_db
def test_match_str_representation(match):
    assert str(match) == 'John Client ↔ Alice Volunteer'

@pytest.mark.django_db
def test_send_request_to_volunteer(match):
    match.send_request_to_volunteer()

    assert match.client_accepted is True
    assert match.client_accepted_at is not None
    assert match.status == 'SUGGESTED'

@pytest.mark.django_db
def test_accept_by_volunteer(match):
    match.status = 'SUGGESTED'
    match.client_accepted = True
    match.client_accepted_at = timezone.now()
    match.save()

    match.accept_by_volunteer()

    assert match.volunteer_accepted is True
    assert match.volunteer_accepted_at is not None
    assert match.status == 'ACCEPTED'

@pytest.mark.django_db
def test_reject_match(match):
    match.reject()
    assert match.status == 'REJECTED'

@pytest.mark.django_db
def test_update_status_both_accepted(match):
    match.status = 'SUGGESTED'
    match.client_accepted = True
    match.client_accepted_at = timezone.now()
    match.volunteer_accepted = True
    match.volunteer_accepted_at = timezone.now()

    match.update_status()
    assert match.status == 'ACCEPTED'

@pytest.mark.django_db
def test_match_ordering(client_user, volunteer_user):
    _, client_profile = client_user

    # second volunteer
    user2 = User.objects.create_user(
        email='volunteer2@test.com',
        password='testpass123',
        role='VOLUNTEER',
        full_name='Volunteer 2'
    )
    volunteer2 = VolunteerProfile.objects.create(
        user=user2,
        forename='Volunteer',
        surname='2',
        gender='F',
        address_line1='789 High St',
        city='London',
        postcode='SW1A 1AA',
        date_of_birth=date(1985, 5, 15),
        emergency_contact_name='Contact',
        emergency_contact_phone='+44712345681',
        emergency_contact_relationship='Friend',
        profile_completed=True
    )

    Match.objects.create(client=client_profile, volunteer=volunteer2, compatibility_score=75)
    Match.objects.create(client=client_profile, volunteer=volunteer_user[1], compatibility_score=50)

    matches = Match.objects.filter(client=client_profile).order_by('-compatibility_score')

    assert matches[0].compatibility_score == 75
    assert matches[1].compatibility_score == 50

# POSTCODE TESTS
def test_get_postcode_area():
    assert get_postcode_area('SW1A 2AA') == 'SW1A'
    assert get_postcode_area('sw1a 2aa') == 'SW1A'
    assert get_postcode_area('E1 6AN') == 'E1'
    assert get_postcode_area('') == ''
    assert get_postcode_area(None) == ''


def test_postcode_match_score():
    assert postcode_match_score('SW1A 2AA', 'SW1A 1AA') == 10
    assert postcode_match_score('SW1A 2AA', 'E1 6AN') == 5
    assert postcode_match_score(None, None) == 0

# PREFERENCE MATCHING
def test_preference_match_no_preferences():
    score, details = preference_match_score(None, None)
    assert score == 0
    assert details == {}

def test_preference_match_language_overlap():
    client = type('obj', (), {
        'preferred_languages': ['EN', 'ES'],
        'preferred_days': [],
        'preferred_times': [],
        'preferred_tasks': []
    })()

    volunteer = type('obj', (), {
        'preferred_languages': ['EN'],
        'preferred_days': [],
        'preferred_times': [],
        'preferred_tasks': [],
        'preferred_gender': '',
        'volunteer': type('obj', (), {'gender': 'M'})()
    })()

    score, details = preference_match_score(client, volunteer)
    assert 'languages' in details
    assert score > 0

def test_preference_match_gender():
    client = type('obj', (), {
        'preferred_languages': [],
        'preferred_days': [],
        'preferred_times': [],
        'preferred_tasks': [],
        'preferred_gender': 'F'
    })()

    volunteer = type('obj', (), {
        'preferred_languages': [],
        'preferred_days': [],
        'preferred_times': [],
        'preferred_tasks': [],
        'preferred_gender': '',
        'volunteer': type('obj', (), {'gender': 'F'})()
    })()

    score, details = preference_match_score(client, volunteer)
    assert details['gender'] == 10

# MATCHING ALGORITHM
@pytest.mark.django_db
def test_calculate_score(client_user, volunteer_user):
    _, client_profile = client_user
    _, volunteer_profile = volunteer_user

    score, notes, breakdown = calculate_score(client_profile, volunteer_profile)

    assert 0 <= score <= 100
    assert 'Location:' in notes
    assert 'Preferences:' in notes

@pytest.mark.django_db
def test_generate_matches_for_client(client_user):
    _, client_profile = client_user

    for i in range(3):
        user = User.objects.create_user(
            email=f'vol{i}@test.com',
            password='testpass123',
            role='VOLUNTEER',
            full_name=f'Volunteer {i}'
        )
        VolunteerProfile.objects.create(
            user=user,
            forename='Vol',
            surname=str(i),
            gender='F',
            address_line1='Test',
            city='London',
            postcode='SW1A 1AA',
            date_of_birth=date(1985, 5, 15),
            emergency_contact_name='Contact',
            emergency_contact_phone='+44712345681',
            emergency_contact_relationship='Friend',
            profile_completed=True
        )

    generate_matches_for_client(client_profile, min_score=0)

    assert Match.objects.filter(client=client_profile).count() > 0

# FORM TESTS
def test_form_valid():
    assert RespondToMatchForm({'response': 'accept'}).is_valid()
    assert RespondToMatchForm({'response': 'reject'}).is_valid()

def test_form_invalid():
    assert not RespondToMatchForm({'response': 'invalid'}).is_valid()
    assert not RespondToMatchForm({}).is_valid()

# VIEW TESTS
@pytest.mark.django_db
def test_match_detail_requires_login(client, match):
    url = reverse('matching:match_detail', args=[match.id])
    response = client.get(url)
    assert response.status_code == 302

@pytest.mark.django_db
def test_client_can_view_match_detail(client, client_user, match):
    user, _ = client_user
    client.login(email=user.email, password='testpass123')

    url = reverse('matching:match_detail', args=[match.id])
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_volunteer_cannot_view_pending_match(client, volunteer_user, match):
    user, _ = volunteer_user
    client.login(email=user.email, password='testpass123')

    url = reverse('matching:match_detail', args=[match.id])
    response = client.get(url)
    assert response.status_code == 302

@pytest.mark.django_db
def test_volunteer_can_view_suggested_match(client, volunteer_user, match):
    user, _ = volunteer_user

    match.status = 'SUGGESTED'
    match.save()

    client.login(email=user.email, password='testpass123')
    url = reverse('matching:match_detail', args=[match.id])
    response = client.get(url)

    assert response.status_code == 200

@pytest.mark.django_db
def test_client_can_send_request(client, client_user, match):
    user, _ = client_user
    client.login(email=user.email, password='testpass123')

    url = reverse('matching:respond_to_match', args=[match.id])
    client.post(url, {'response': 'accept'})

    match.refresh_from_db()
    assert match.status == 'SUGGESTED'
    assert match.client_accepted

@pytest.mark.django_db
def test_volunteer_can_accept(client, volunteer_user, match):
    user, _ = volunteer_user

    match.status = 'SUGGESTED'
    match.client_accepted = True
    match.client_accepted_at = timezone.now()
    match.save()

    client.login(email=user.email, password='testpass123')
    url = reverse('matching:respond_to_match', args=[match.id])
    client.post(url, {'response': 'accept'})

    match.refresh_from_db()
    assert match.status == 'ACCEPTED'